"""List boot environments cli"""

import sys
from typing import Optional, List

import click

import pyzfscmds.utility as zfs_utility
import pyzfscmds.system.agnostic

import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger


def format_boot_environment(be_list_line: list,
                            scripting: Optional[bool],
                            widths: List[int]) -> str:
    """
    Formats list into column separated string with tabs if scripting.
    """
    if scripting:
        return "\t".join(be_list_line)
    else:
        fmt_line = ["{{: <{width}}}".format(width=w+1) for w in widths]
        return " ".join(fmt_line).format(*be_list_line)


def configure_boot_environment_list(be_root: str,
                                    columns: list,
                                    scripting: Optional[bool]) -> list:
    """
    Converts a list of boot environments with their properties to be printed
    to a list of column separated strings.
    """
    boot_environments = zedenv.lib.be.list_boot_environments(be_root, columns)

    columns.insert(1, "active")

    unformatted_boot_environments = []

    # Set minimum column width to name of column plus one
    widths = [len(l)+1 for l in columns]

    for env in boot_environments:
        if not zfs_utility.is_snapshot(env[0]):
            origin = f'@{env[1].split("@")[1]}' if zfs_utility.is_snapshot(env[1]) else env[1]
            active = ""
            if pyzfscmds.system.agnostic.mountpoint_dataset("/") == env[0]:
                active = "N"

            if zedenv.lib.check.bootfs_for_pool(
                    zedenv.lib.be.dataset_pool(env[0])) == env[0]:
                active += "R"

            unformatted_boot_environments.append(
                [zfs_utility.dataset_child_name(env[0])] + [active] + [origin] + env[2:])

    # Check for largest column entry and use as width.
    for ube in unformatted_boot_environments:
        for i, w in enumerate(ube):
            if len(w) > widths[i]:
                widths[i] = len(w)

    formatted_boot_environments = []

    if not scripting:
        formatted_boot_environments.append(format_boot_environment(columns, scripting, widths))

    formatted_boot_environments.extend(
        [format_boot_environment(b, scripting, widths) for b in unformatted_boot_environments])

    return formatted_boot_environments


def zedenv_list(verbose: Optional[bool],
                alldatasets: Optional[bool],
                spaceused: Optional[bool],
                scripting: Optional[bool],
                snapshots: Optional[bool],
                be_root: str):
    """
    Main list command. Separate for testing.
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

    boot_environments = configure_boot_environment_list(be_root, columns, scripting)

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
def cli(verbose: Optional[bool],
        alldatasets: Optional[bool],
        spaceused: Optional[bool],
        scripting: Optional[bool],
        snapshots: Optional[bool]):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        sys.exit(err)

    zedenv_list(verbose,
                alldatasets,
                spaceused,
                scripting,
                snapshots,
                zedenv.lib.be.root())
