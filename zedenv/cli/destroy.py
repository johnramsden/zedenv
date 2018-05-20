"""List boot environments cli"""

import re
import sys
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

    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Found snapshots to promote:\n{split_promote_snaps}"
    }, True)

    target = re.compile(r'\b' + destroy_dataset + r'(@|/.*@).*' + r'\b')
    return [ds[0] for ds in split_promote_snaps if target.match(ds[1])]


def get_origin_snapshots(be_pool: str, destroy_dataset: str) -> list:
    origin_all_snaps = None
    try:
        origin_all_snaps = pyzfscmds.cmd.zfs_list(
            be_pool, recursive=True,
            columns=['origin'], zfs_types=['filesystem', 'snapshot', 'volume'])
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to list origin snapshots for '{be_pool}'.\n{e}"
        }, exit_on_error=True)

    split_snaps = zedenv.lib.be.split_zfs_output(origin_all_snaps)

    target = re.compile(r'\b' + destroy_dataset + r'(@|/.*@).*' + r'\b')

    return [ds[1] for ds in split_snaps if target.match(ds[0])]


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
            "message": f"Cannot destroy active boot environment '{target}'."
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
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Found snapshots to promote:\n{promote_snaps}"
            }, verbose)

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

        # Get origin snapshots

            # origin_snaps = get_origin_snapshots(be_pool, destroy_dataset)
            #
            # ZELogger.verbose_log({
            #     "level": "INFO",
            #     "message": f"Found origin snapshots':\n{origin_snaps}"
            # }, verbose)


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
