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


@click.command(name="Unmount",
               help="Unount a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--existing', '-e',
              help="Use existing boot environment as source.")
@click.argument('boot_environment')
def cli(boot_environment, verbose):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        sys.exit(err)
