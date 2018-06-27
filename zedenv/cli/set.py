"""Get boot environment properties cli"""

from typing import Optional

import click

import pyzfscmds.system.agnostic
import pyzfscmds.cmd

import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger


def zedenv_set(verbose: Optional[bool], zedenv_properties: Optional[list], be_root: str):

    for prop in zedenv_properties:
        try:
            pyzfscmds.cmd.zfs_set(be_root, prop)
        except RuntimeError:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to set zedenv property '{prop}'\n"
            }, exit_on_error=True)

        if verbose:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Set '{prop}' successfully"
            }, verbose)


@click.command(name="set",
               help="Set boot environment properties.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.argument('zedenv_properties', nargs=-1, required=True)
def cli(verbose: Optional[bool],
        zedenv_properties: Optional[list]):

    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)

    zedenv_set(verbose, zedenv_properties, zedenv.lib.be.root())
