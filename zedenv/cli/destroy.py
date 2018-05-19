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
                   noconfirm: Optional[bool]):
    """
    Put actual function to be called in this separate function to allow easier testing.
    """
    boot_environment_dataset = f"{be_root}/{target}"

    if zedenv.lib.be.is_current_boot_environment(target):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Cannot destroy active boot environment '{target}'."
        }, exit_on_error=True)

    if not noconfirm:
        click.confirm(f"Do you really want to destroy '{target}'?\n"
                      "This action will be permanent.\n\n"
                      f"Destroy '{boot_environment_dataset}'?\n", abort=True)

    if pyzfscmds.utility.is_snapshot(boot_environment_dataset):
        try:
            pyzfscmds.cmd.zfs_destroy_snapshot(boot_environment_dataset)
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Snapshot may be origin for other boot environment.\n{e}"
            }, exit_on_error=True)
        ZELogger.verbose_log(
            {"level": "INFO", "message": f"Destroyed '{boot_environment_dataset}"}, verbose)
    # else:
    #     if pyzfscmds.utility.is_clone(boot_environment_dataset):


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
@click.argument('boot_environment')
def cli(boot_environment: str,
        verbose: Optional[bool],
        unmount: Optional[bool],
        noconfirm: Optional[bool]):

    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        sys.exit(err)

    zedenv_destroy(boot_environment,
                   zedenv.lib.be.root(),
                   pyzfscmds.system.agnostic.mountpoint_dataset("/"),
                   verbose,
                   unmount,
                   noconfirm)
