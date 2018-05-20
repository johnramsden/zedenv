"""List boot environments cli"""

import sys
from typing import Optional

import click

import pyzfscmds.utility as zfs_utility
import pyzfscmds.cmd
import pyzfscmds.system.agnostic

import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger


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
    boot_environment_dataset = f"{be_root}/{target}"
    be_pool = zedenv.lib.be.dataset_pool(boot_environment_dataset)

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

    if not noconfirm:
        click.confirm(f"Do you really want to destroy '{target}'?\n"
                      "This action will be permanent.\n\n"
                      f"Destroy '{boot_environment_dataset}'?", abort=True)
        click.echo()

    if pyzfscmds.utility.is_snapshot(boot_environment_dataset):
        if not noop:
            try:
                pyzfscmds.cmd.zfs_destroy_snapshot(boot_environment_dataset)
            except RuntimeError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Snapshot may be origin for other boot environment.\n{e}"
                }, exit_on_error=True)
        ZELogger.verbose_log(
            {"level": "INFO", "message": f"Destroyed '{boot_environment_dataset}"}, verbose)
    else:
        if pyzfscmds.utility.is_clone(boot_environment_dataset):
            ZELogger.verbose_log({
                "level": "INFO",
                "message": (f"Boot environment '{target}' is a clone.\n"
                            "Checking to make sure there are no dependant clones to promote.\n")
            }, verbose)

            # Get origin snapshots

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
            origin_snaps = [c[0] for c in split_snaps if c[0] != '-']

            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Found origin snapshots for '{be_pool}':\n{origin_snaps}"
            }, verbose)


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
