"""List boot environments cli"""

import sys
from typing import Optional

import click

import pyzfscmds.utility as zfs_utility
import pyzfscmds.system.agnostic

import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger


def zedenv_destroy(boot_environment: str,
                   be_root: str,
                   root_dataset: str,
                   verbose: Optional[bool],
                   unmount: Optional[bool]):
    """
    Put actual function to be called in this separate function to allow easier testing.
    """
    ZELogger.verbose_log({
        "level": "INFO", "message": f"Destroying Boot Environment: '{boot_environment}'\n"
    }, verbose)

    boot_environment_dataset = f"{be_root}/{boot_environment}"

    if zedenv.lib.be.is_current_boot_environment(boot_environment):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Cannot destroy active boot environment '{boot_environment}'."
        }, exit_on_error=True)


@click.command(name="destroy",
               help="Destroy a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--unmount', '-F',
              is_flag=True,
              help="Unmount BE automatically.")
@click.argument('boot_environment')
def cli(boot_environment: str,
        verbose: Optional[bool],
        unmount: Optional[bool]):

    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        sys.exit(err)

    zedenv_destroy(boot_environment,
                   zedenv.lib.be.root(),
                   pyzfscmds.system.agnostic.mountpoint_dataset("/"),
                   verbose,
                   unmount)
