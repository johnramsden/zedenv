"""List boot environments cli"""

import sys

from typing import Optional

import click
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility as zfs_utility

import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger


@click.command(name="rename",
               help="Rename a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.argument('boot_environment')
@click.argument('new_boot_environment')
def cli(boot_environment, new_boot_environment, verbose):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)
