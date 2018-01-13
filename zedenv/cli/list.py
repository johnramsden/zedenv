"""List boot environments cli"""

import click

from zedenv.lib.zfs.command import ZFS
import zedenv.lib.zfs.utility as zfs_utility
import zedenv.lib.zfs.linux as zfs_linux

import zedenv.lib.boot_environment as be

from zedenv.lib.logger import ZELogger


def configure_boot_environment_list() -> list:
    boot_environments = be.list_boot_environments(be.get_root())

    formatted_boot_environments = list()

    for env in boot_environments:
        if not zfs_utility.is_snapshot(env[0]):
            boot_env = [zfs_utility.dataset_child_name(env[0])] + env[1:]
            formatted_boot_environments.append(boot_env)

    for fenv in formatted_boot_environments:
        # set the columns to a minimum of 20 characters and align text to right.
        print("{: <20} {: <20} {: <20} {: <20} {: <20} {: <20} {: <20} {: <20}".format(*fenv))

    return formatted_boot_environments


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

    boot_environments = configure_boot_environment_list()

    # Headers:
    # BE              Active Mountpoint  Space Created
    for list_output in boot_environments:
        ZELogger.log({"level": "INFO", "message": list_output}, verbose)

