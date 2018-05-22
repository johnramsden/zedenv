"""List boot environments cli"""

import re
import sys
import datetime
from typing import Optional

import click

import pyzfscmds.utility as zfs_utility
import pyzfscmds.cmd
import pyzfscmds.system.agnostic

import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger


def get_promote_snapshots(be_pool: str, destroy_dataset: str) -> list:
    """
    Look for clone we need to promote because they're dependent on snapshots
    """
    promote_snaps = None
    try:
        promote_snaps = pyzfscmds.cmd.zfs_list(
            be_pool, recursive=True,
            columns=['name', 'origin'], zfs_types=['filesystem', 'snapshot', 'volume'])
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to list snapshots for promote in '{be_pool}'.\n{e}"
        }, exit_on_error=True)

    split_promote_snaps = zedenv.lib.be.split_zfs_output(promote_snaps)

    target = re.compile(r'\b' + destroy_dataset + r'(@|/.*@).*' + r'\b')
    return [ds[0] for ds in split_promote_snaps if target.match(ds[1])]


def get_origin_snapshots(destroy_dataset: str) -> list:
    origin_all_snaps = None
    try:
        origin_all_snaps = pyzfscmds.cmd.zfs_list(
            destroy_dataset, recursive=True,
            columns=['origin'], zfs_types=['filesystem', 'snapshot', 'volume'])
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to list origin snapshots for '{destroy_dataset}'.\n{e}"
        }, exit_on_error=True)

    split_snaps = zedenv.lib.be.split_zfs_output(origin_all_snaps)
    return [ds[0].rstrip() for ds in split_snaps if ds[0].rstrip() != '-']

def get_clone_origin(destroy_dataset: str) -> Optional[str]:
    # Get origin snapshots
    origin_snaps = get_origin_snapshots(destroy_dataset)

    origin_property = None
    try:
        origin_property = pyzfscmds.cmd.zfs_get(destroy_dataset,
                                                columns=['value'],
                                                properties=['origin']).rstrip()
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to get origin of {destroy_dataset}\n{e}\n"
        }, exit_on_error=True)

    # Remove any newline chars
    origin_property = origin_property.rstrip()

    origin_datetime = None
    try:
        origin_datetime = datetime.datetime.strptime(
            origin_property.split('@')[1], "%Y-%m-%d-%H-%f")
    except ValueError:
        try:
            origin_datetime = datetime.datetime.strptime(
                origin_property.split('@')[1].split("-", 1)[1], "%Y-%m-%d-%H-%f")
        except ValueError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to parse time from origin {origin_property}\n"
            }, exit_on_error=True)

    creation_property = None
    try:
        creation_property = pyzfscmds.cmd.zfs_get(destroy_dataset,
                                                  columns=['value'],
                                                  properties=['creation'])
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to get creation of {creation_property}\n{e}\n"
        }, exit_on_error=True)

    creation_property = creation_property.rstrip()

    creation_datetime = None
    try:
        creation_datetime = datetime.datetime.strptime(creation_property,
                                                       "%a %b %d %H:%M %Y")
    except ValueError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to parse time from origin {origin_property}\n{e}"
        }, exit_on_error=True)

    return origin_property if origin_datetime != creation_datetime else None


def zedenv_destroy(target: str,
                   be_root: str,
                   root_dataset: str,
                   verbose: Optional[bool],
                   unmount: Optional[bool],
                   noconfirm: Optional[bool],
                   noop: Optional[bool]):
    """
    Put actual function to be called in this separate function to allow easier testing.
    """
    destroy_dataset = f"{be_root}/{target}"
    ds_is_snapshot = pyzfscmds.utility.is_snapshot(destroy_dataset)
    be_pool = zedenv.lib.be.dataset_pool(
        destroy_dataset,
        zfs_type='filesystem' if not ds_is_snapshot else 'snapshot')

    if be_pool is None:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"The destroy target {target} does not exist."
        }, exit_on_error=True)

    if zedenv.lib.be.is_current_boot_environment(target):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Cannot destroy the active boot environment '{target}'."
        }, exit_on_error=True)

    if pyzfscmds.system.agnostic.dataset_mountpoint(destroy_dataset) == "/":
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Cannot destroy current root dataset environment '{target}'."
        }, exit_on_error=True)

    if not noconfirm:
        click.confirm(f"Do you really want to destroy '{target}'?\n"
                      "This action will be permanent.\n\n"
                      f"Destroy '{destroy_dataset}'?", abort=True)
        click.echo()

    if ds_is_snapshot:
        if not noop:
            try:
                pyzfscmds.cmd.zfs_destroy_snapshot(destroy_dataset)
            except RuntimeError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Snapshot may be origin for other boot environment.\n{e}"
                }, exit_on_error=True)
        ZELogger.verbose_log(
            {"level": "INFO", "message": f"Destroyed '{destroy_dataset}"}, verbose)
    else:
        if pyzfscmds.utility.is_clone(destroy_dataset):
            ZELogger.verbose_log({
                "level": "INFO",
                "message": (f"Boot environment '{target}' is a clone.\n"
                            "Checking to make sure there are no dependant clones to promote.\n")
            }, verbose)

            # Get and promote snapshots
            promote_snaps = get_promote_snapshots(be_pool, destroy_dataset)

            for ds in promote_snaps:
                if not noop:
                    try:
                        pyzfscmds.cmd.zfs_promote(ds)
                    except RuntimeError:
                        ZELogger.log({
                            "level": "EXCEPTION",
                            "message": f"Failed to promote {ds}\n{e}\n"
                        }, exit_on_error=True)
                ZELogger.verbose_log(
                    {"level": "INFO", "message": f"Promoted {ds}.\n"}, verbose)

            """
            Find destroyable:
            There's probably a better way to match snapshots that can be destroyed,
            for now this will do
            """

            clone_origin = get_clone_origin(destroy_dataset)
            if clone_origin:
                if not noconfirm:
                    click.echo(f"The origin snapshot '{clone_origin.split('@')[1]}' "
                               f"for the boot environment '{target}' "
                               f"still exists, do you want to destroy it? "
                               f"This action will be permanent.\n")
                    destroy_origin_snapshot = click.confirm(f"Destroy '{clone_origin}'?")
                    click.echo()
                else:
                    destroy_origin_snapshot = True

                if not destroy_origin_snapshot:
                    click.echo(
                        f"The origin snapshot '{clone_origin.split('@')[1]}' will be kept.")








@click.command(name="destroy",
               help="Destroy a boot environment or snapshot.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--unmount', '-F',
              is_flag=True,
              help="Unmount BE automatically.")
@click.option('--noconfirm', '-y',
              is_flag=True,
              help="Destroy without prompt asking for confirmation.")
@click.option('--noop', '-n',
              is_flag=True,
              help="Print what would be destroyed.")
@click.argument('boot_environment')
def cli(boot_environment: str,
        verbose: Optional[bool],
        unmount: Optional[bool],
        noconfirm: Optional[bool],
        noop: Optional[bool]):

    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        sys.exit(err)

    zedenv_destroy(boot_environment,
                   zedenv.lib.be.root(),
                   pyzfscmds.system.agnostic.mountpoint_dataset("/"),
                   verbose,
                   unmount,
                   noconfirm,
                   noop)
