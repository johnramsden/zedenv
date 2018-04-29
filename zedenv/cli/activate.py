"""List boot environments cli"""

import click
import pyzfsutils.lib.zfs.linux as zfs_linux
import pyzfsutils.lib.zfs.utility as zfs_utility
from pyzfsutils.lib.zfs.command import ZFS

import zedenv.lib.boot_environment as be
from zedenv.lib.logger import ZELogger


def zedenv_activate(boot_environment, verbose):
    """
    :Parameters:
      boot_environment : str
        Name of boot environment to activate
      verbose : bool
        Print information verbosely.
    :return:
    """

    ZELogger.verbose_log({
        "level": "INFO", "message": "Activating Boot Environment:\n"
    }, verbose)


@click.command(name="activate",
               help="Activate a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.argument('boot_environment')
def cli(boot_environment, verbose):
    zedenv_activate(boot_environment, verbose)
