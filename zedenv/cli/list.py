"""List boot environments cli"""

import click

from zedenv.lib.zfs.command import ZFS
import zedenv.lib.zfs.utility as zfs_utility
import zedenv.lib.zfs.linux as zfs_linux

import zedenv.lib.boot_environment as be

from zedenv.lib.logger import ZELogger



@click.command(name="list",
               help="List all boot environments.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--all', '-a',
              is_flag=True,
              help="Display all datasets.")
@click.option('--spaceused', '-D',
              is_flag=True,
              help="Display the full space usage for each boot environment.")
@click.option('--scripting', '-H',
              is_flag=True,
              help="Scripting output.")
@click.option('--snapshots', '-s',
              is_flag=True,
              help="Display snapshots.")
def cli(verbose, all, spaceused, scripting, snapshots):

    parent_dataset = be.get_root()
    root_dataset = zfs_linux.mount_dataset("/")

    ZELogger.verbose_log({
        "level":   "INFO", "message": "Listing Boot Environments:\n"
    }, verbose)

