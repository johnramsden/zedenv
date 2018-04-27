"""List boot environments cli"""

import click
import pyzfsutils.lib.zfs.utility as zfs_utility

import zedenv.lib.boot_environment as be
from zedenv.lib.logger import ZELogger


def format_boot_environment(be_list_line: list) -> str:
    """
    Formats list into column separated string.
    """
    return " ".join(["{: <16}"] * len(be_list_line)).format(*be_list_line)


def configure_boot_environment_list(be_root, columns: list) -> list:
    """
    Converts a list of boot environments with their properties to be printed
    to a list of column separated strings.
    """
    boot_environments = be.list_boot_environments(be_root, columns)

    formatted_boot_environments = list()

    for env in boot_environments:
        if not zfs_utility.is_snapshot(env[0]):
            boot_env = [zfs_utility.dataset_child_name(env[0])] + env[1:]
            formatted_boot_environments.append(boot_env)

    return [format_boot_environment(b) for b in formatted_boot_environments]


def zedenv_list(verbose, all_datasets, spaceused, scripting, snapshots, be_root):
    """
    But actual function to be called in this separate function to allow easier testing.
    """
    ZELogger.verbose_log({
        "level": "INFO", "message": "Listing Boot Environments:\n"
    }, verbose)

    columns = ["name"]

    if spaceused:
        columns.extend(["used", "usedds", "usedbysnapshots", "usedrefreserv", "refer"])

    """
    TODO:
    if all_datasets:

    if snapshots:
    """

    columns.extend(["origin", "creation"])

    boot_environments = configure_boot_environment_list(be_root, columns)

    if not scripting:
        list_header = format_boot_environment(columns)
        ZELogger.log({"level": "INFO", "message": list_header}, verbose)

    for list_output in boot_environments:
        ZELogger.log({"level": "INFO", "message": list_output}, verbose)


@click.command(name="list",
               help="List all boot environments.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--alldatasets', '-a',
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
def cli(verbose, alldatasets, spaceused, scripting, snapshots):
    zedenv_list(verbose, alldatasets, spaceused, scripting, snapshots, be.root())
