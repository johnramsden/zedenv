"""List boot environments cli"""
import errno
import re
import sys
import datetime

import click

import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility as zfs_utility

from typing import Optional

import zedenv.lib.configure
import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger
import zedenv.lib.system


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

    origin_property = None
    try:
        origin_property = pyzfscmds.cmd.zfs_get(destroy_dataset,
                                                columns=['value'],
                                                properties=['origin'])
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to get origin of {destroy_dataset}\n{e}\n"
        }, exit_on_error=True)

    # Remove any newline chars
    origin_property = origin_property.rstrip()

    origin_datetime = None
    try:
        origin_datetime = zedenv.lib.system.parse_time(origin_property)
    except ValueError:
        try:
            origin_datetime = zedenv.lib.system.parse_time(
                origin_property.split('@')[1])
        except ValueError:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to parse time from origin {origin_property}\n"
            }, exit_on_error=True)

    creation_property = None
    try:
        creation_property = pyzfscmds.cmd.zfs_get(destroy_dataset,
                                                  columns=['value'],
                                                  properties=['creation'],
                                                  env_variables_override={"LC_ALL": "C"})
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to get creation of {creation_property}\n{e}\n"
        }, exit_on_error=True)

    creation_property = creation_property.rstrip()

    creation_datetime = None
    try:
        creation_datetime = zedenv.lib.system.parse_time(creation_property,
                                                         fmt="%a %b %d %H:%M %Y")
    except ValueError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to parse time from origin {origin_property}\n{e}"
        }, exit_on_error=True)

    return origin_property if origin_datetime != creation_datetime else None


def promote_origins(destroy_dataset, be_pool, origin_snaps, noop, verbose):
    # promote dependents of origins used by destroy_dataset
    origins = None
    try:
        origins = pyzfscmds.cmd.zfs_list(
            be_pool, recursive=True,
            columns=['name', 'origin'], zfs_types=['filesystem', 'snapshot', 'volume'])
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to list origins of '{destroy_dataset}'.\n"
        }, exit_on_error=True)
    origins_list = zedenv.lib.be.split_zfs_output(origins)

    for ors in origin_snaps:
        for ol in origins_list:
            if ors == ol[1].rstrip():
                if not noop:
                    try:
                        pyzfscmds.cmd.zfs_promote(ol[0].rstrip())
                    except RuntimeError:
                        ZELogger.log({
                            "level": "EXCEPTION",
                            "message": f"Failed to promote {ol[0].rstrip()}\n"
                        }, exit_on_error=True)
                ZELogger.verbose_log(
                    {"level": "INFO", "message": f"Promoted {ol[0].rstrip()}.\n"}, verbose)


def destroy_origin_snapshots(destroy_dataset, be_pool, origin_snaps, noop, verbose):
    # destroy origin snapshots used by destroy_dataset
    snapshots = None
    try:
        snapshots = pyzfscmds.cmd.zfs_list(be_pool,
                                           recursive=True,
                                           columns=['name'],
                                           zfs_types=['snapshot'])
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to list origins snapshots of '{destroy_dataset}'.\n"
        }, exit_on_error=True)
    snapshots_list = zedenv.lib.be.split_zfs_output(snapshots)

    for ors in origin_snaps:
        for ol in snapshots_list:
            snap = ol[0].rstrip()
            if ors == snap:
                if not noop:
                    try:
                        pyzfscmds.cmd.zfs_destroy_snapshot(snap)
                    except RuntimeError:
                        ZELogger.log({
                            "level": "EXCEPTION",
                            "message": f"Failed to destroy {snap}\n"
                        }, exit_on_error=True)
                ZELogger.verbose_log(
                    {"level": "INFO", "message": f"Destroyed {snap}.\n"}, verbose)


def destroy_element(target: str,
                    dataset: str,
                    is_snapshot: bool,
                    verbose: Optional[bool],
                    noconfirm: Optional[bool],
                    noop: Optional[bool]):
    if is_snapshot:
        if not noop:
            try:
                pyzfscmds.cmd.zfs_destroy_snapshot(dataset)
            except RuntimeError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Snapshot may be origin for other boot environment.\n{e}"
                }, exit_on_error=True)
        ZELogger.verbose_log(
            {"level": "INFO", "message": f"Destroyed '{dataset}"}, verbose)
    else:
        destroy_origin_snapshot = True
        origin_snaps = None
        if pyzfscmds.utility.is_clone(dataset):
            ZELogger.verbose_log({
                "level": "INFO",
                "message": (f"Boot environment '{target}' is a clone.\n"
                            "Checking to make sure there are no dependant clones to promote.\n")
            }, verbose)

            # Get and promote snapshots
            pool = zedenv.lib.be.dataset_pool(dataset)
            promote_snaps = get_promote_snapshots(pool, dataset)

            for ds in promote_snaps:
                if not noop:
                    try:
                        pyzfscmds.cmd.zfs_promote(ds)
                    except RuntimeError as e:
                        ZELogger.log({
                            "level": "EXCEPTION",
                            "message": f"Failed to promote {ds}\n{e}\n"
                        }, exit_on_error=True)
                    else:
                        ZELogger.verbose_log(
                            {"level": "INFO", "message": f"Promoted {ds}.\n"}, verbose)

            """
            Find destroyable:
            There's probably a better way to match snapshots that can be destroyed,
            for now this will do
            """
            origin_snaps = get_origin_snapshots(dataset)
            clone_origin = get_clone_origin(dataset)
            if clone_origin:
                if not noconfirm:
                    click.echo(f"The origin snapshot '{clone_origin.split('@')[1]}' "
                               f"for the boot environment '{target}' "
                               f"still exists, do you want to destroy it? "
                               f"This action will be permanent.\n")
                    destroy_origin_snapshot = click.confirm(f"Destroy '{clone_origin}'?")
                    click.echo()

                if not destroy_origin_snapshot:
                    click.echo(
                        f"The origin snapshot '{clone_origin.split('@')[1]}' will be kept.")

        # Destroy the boot environment
        if not noop:
            try:
                pyzfscmds.cmd.zfs_destroy(dataset,
                                          recursive_children=True)
            except RuntimeError:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Failed to destroy {dataset}\n"
                }, exit_on_error=True)

        try:
            # TODO: Why is this necessary?
            is_still_clone = pyzfscmds.utility.is_clone(dataset)
        except RuntimeError:
            is_still_clone = False

        if is_still_clone:
            promote_origins(dataset, pool, origin_snaps, noop, verbose)

        if destroy_origin_snapshot:
            destroy_origin_snapshots(dataset, pool, origin_snaps, noop, verbose)


def zedenv_destroy(target: str,
                   be_root: str,
                   root_dataset: str,
                   bootloader: Optional[str],
                   verbose: Optional[bool],
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

    current_be = None
    zpool = zedenv.lib.be.dataset_pool(destroy_dataset)
    try:
        current_be = pyzfscmds.utility.dataset_child_name(
            zedenv.lib.be.bootfs_for_pool(zpool))
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to get active boot environment'\n"
        }, exit_on_error=True)

    if current_be == target:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Cannot destroy current active environment '{target}'."
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

    bootloader_set = zedenv.lib.be.get_property(destroy_dataset, "org.zedenv:bootloader")
    if not bootloader and bootloader_set:
        bootloader = bootloader_set if bootloader_set != '-' else None

    bootloader_plugin = None
    if bootloader:
        bootloader_plugin = zedenv.lib.configure.get_bootloader(
            target, current_be, bootloader, verbose, noconfirm, noop, be_root)
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Using plugin {bootloader}\n"
        }, verbose)

    # Destroy the root boot environment
    destroy_element(target, destroy_dataset, ds_is_snapshot, verbose, noconfirm, noop)

    # Destroy the dataset for the kernel and ramdisk files if a separate ZFS boot pool is used
    if zedenv.lib.be.extra_bpool():
        boot_dataset = pyzfscmds.system.agnostic.mountpoint_dataset("/boot")
        m = re.search(r"(.*)/zedenv-", boot_dataset)
        if m:
            destroy_dataset = f"{m.group(1)}/zedenv-{target}"
            ds_is_snapshot = pyzfscmds.utility.is_snapshot(destroy_dataset)
            destroy_element(target, destroy_dataset, ds_is_snapshot, verbose, noconfirm, noop)
        else:
            ZELogger.log({
                "level": "WARNING",
                "message": (f"Failed to determine a valid path from '{boot_dataset}'")
            })

    if bootloader:
        try:
            bootloader_plugin.post_destroy(target)
        except AttributeError:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Tried to run plugin's 'post destroy', not implemented.\n"
            }, verbose)

    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Destroyed boot environment {target} successfully.\n"
    }, verbose)


@click.command(name="destroy",
               help="Destroy a boot environment or snapshot.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--noconfirm', '-y',
              is_flag=True,
              help="Destroy without prompt asking for confirmation.")
@click.option('--noop', '-n',
              is_flag=True,
              help="Print what would be destroyed but don't apply.")
@click.option('--bootloader', '-b',
              help="Use bootloader type.")
@click.argument('boot_environment')
def cli(boot_environment: str,
        verbose: Optional[bool],
        bootloader: Optional[str],
        # unmount: Optional[bool],
        noconfirm: Optional[bool],
        noop: Optional[bool]):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)

    try:
        with zedenv.lib.check.Pidfile():

            boot_environment_root = zedenv.lib.be.root()

            bootloader_set = zedenv.lib.be.get_property(
                boot_environment_root, "org.zedenv:bootloader")
            if not bootloader and bootloader_set:
                bootloader = bootloader_set if bootloader_set != '-' else None

            zedenv_destroy(boot_environment,
                           boot_environment_root,
                           pyzfscmds.system.agnostic.mountpoint_dataset("/"),
                           bootloader,
                           verbose,
                           noconfirm,
                           noop)

    except IOError as e:
        if e[0] == errno.EPERM:
            ZELogger.log({
                "level": "EXCEPTION", "message":
                    "You need root permissions to destroy"
            }, exit_on_error=True)
    except zedenv.lib.check.ProcessRunningException as pr:
        ZELogger.log({
            "level": "EXCEPTION", "message":
                f"Already running zedenv.\n {pr}"
        }, exit_on_error=True)
