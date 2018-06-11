"""List boot environments cli"""

import sys

from typing import Optional

import click
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility as zfs_utility

import zedenv.lib.be
import zedenv.lib.check
import zedenv.lib.system
from zedenv.lib.logger import ZELogger


def zedenv_umount(boot_environment: str, verbose: bool, be_root: str):
    boot_environment_dataset = f"{be_root}/{boot_environment}"
    child_datasets_unformatted = None
    try:
        child_datasets_unformatted = pyzfscmds.cmd.zfs_list(boot_environment_dataset,
                                                            sort_properties_descending=['name'],
                                                            recursive=True,
                                                            columns=['name'])
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to get list of datasets for '{boot_environment}'.\n{e}"
        }, exit_on_error=True)

    for d in zedenv.lib.be.split_zfs_output(child_datasets_unformatted):
        mountpoint = pyzfscmds.system.agnostic.dataset_mountpoint(d[0])
        if mountpoint:
            try:
                zedenv.lib.system.umount(mountpoint)
            except RuntimeError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Failed Un-mounting child dataset from '{mountpoint}'.\n{e}"
                }, exit_on_error=True)
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Unmounted {d[0]} from {mountpoint}.\n"
            }, verbose)
        else:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Child dataset {d[0]} wasn't mounted, won't unmount.\n"
            }, verbose)


@click.command(name="umount",
               help="Unmount a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.argument('boot_environment')
def cli(boot_environment: str, verbose: Optional[bool]):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)

    be_root = zedenv.lib.be.root()
    dataset_mountpoint = pyzfscmds.system.agnostic.dataset_mountpoint(
        f"{be_root}/{boot_environment}")

    if not pyzfscmds.utility.dataset_exists(f"{be_root}/{boot_environment}"):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Boot environment doesn't exist {boot_environment}.\n"
        }, exit_on_error=True)

    if dataset_mountpoint == "/":
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Cannot Unmount root dataset.\n"
        }, exit_on_error=True)

    if not dataset_mountpoint:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Boot environment already un-mounted\n"
        }, exit_on_error=True)

    zedenv_umount(boot_environment, verbose, be_root)
