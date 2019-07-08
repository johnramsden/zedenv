"""List boot environments cli"""

import os
import tempfile

from typing import Optional

import click
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility as zfs_utility

import zedenv.lib.be
import zedenv.lib.check
import zedenv.lib.system
from zedenv.lib.logger import ZELogger


def mount_children(child_datasets: list, mountpoint: str, verbose: bool):
    for cd in child_datasets:
        if cd['mountpoint'] == "none" or cd['mountpoint'] == "legacy":
            ZELogger.verbose_log({
                "level": "INFO",
                "message": (f"Skipped mounting dataset {cd['name']} "
                            f"since mountpoint is {cd['mountpoint']}.\n")
            }, verbose)
        else:
            if cd['source'] == 'local':
                child = pyzfscmds.utility.dataset_child_name(cd['name'], check_exists=False)
                new_mount = os.path.join(mountpoint, child.lstrip('/'))
            else:
                new_mount = os.path.join(mountpoint, cd['mountpoint'].lstrip('/'))

            if not os.path.exists(new_mount):
                os.makedirs(new_mount)

            try:
                zedenv.lib.system.zfs_manual_mount(cd['name'], new_mount)
            except RuntimeError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Failed mounting child dataset to '{new_mount}'.\n{e}"
                }, exit_on_error=True)
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Mounted dataset {cd['name']} to '{new_mount}'.\n"
            }, verbose)


def zedenv_mount(boot_environment: str, mountpoint: Optional[str], verbose: bool, be_root: str, check_bpool = True):
    """
    Create a temporary directory and mount a boot environment.
    If an extra argument is given, mount the boot environment at the given mountpoint.
    """

    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Mounting boot environment '{boot_environment}'.\n"
    }, verbose)

    if not mountpoint:
        mountpoint = tempfile.mkdtemp(suffix=f"-{boot_environment}", prefix="zedenv-")
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"No mountpoint given, using a temporary directory {mountpoint}.\n"
        }, verbose)
    else:
        if os.path.ismount(mountpoint):
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"There is already a file system mounted at {mountpoint}"
            }, exit_on_error=True)

        if not os.path.isdir(mountpoint):
            ZELogger.log({
                "level": "EXCEPTION",
                "message": (f"The path'{mountpoint}' is not a directory, "
                            "cannot be used as mountpoint.\n")
            }, exit_on_error=True)
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Mountpoint '{mountpoint}' given, using as mountpoint.\n"
        }, verbose)

    be_dataset = f"{be_root}/{boot_environment}"

    try:
        zedenv.lib.system.zfs_manual_mount(be_dataset, mountpoint)
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed mounting dataset to '{mountpoint}'.\n{e}"
        }, exit_on_error=True)

    ZELogger.verbose_log(
        {"level": "INFO", "message": f"Mounted dataset to '{mountpoint}'.\n"}, verbose)
    if not verbose:
        ZELogger.log({"level": "INFO", "message": mountpoint})

    child_datasets = zedenv.lib.be.list_child_mountpoints(be_dataset)

    if child_datasets:
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Mounting children of '{boot_environment}'.\n"
        }, verbose)
        mount_children(child_datasets, mountpoint, verbose)

    if check_bpool:
        # If a separate ZFS boot pool is used, mount the corresponding dataset to `{mountpoint}/boot`
        if zedenv.lib.be.extra_bpool():
            boot_environment_boot = zedenv.lib.be.root('/boot')
            be_boot_requested = f"{boot_environment_boot}/zedenv-{boot_environment}"
            try:
                zedenv.lib.system.zfs_manual_mount(be_boot_requested, f"{mountpoint}/boot")
            except RuntimeError as e:
                ZELogger.log({
                    "level": "WARNING",
                    "message": f"Failed mounting boot dataset to '{mountpoint}/boot'.\n{e}"
                })


@click.command(name="mount",
               help="Mount a boot environment temporarily.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.argument('boot_environment')
@click.argument('mountpoint', nargs=-1, required=False)
def cli(boot_environment: str, mountpoint: Optional[list], verbose: Optional[bool]):
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

    if dataset_mountpoint:
        if dataset_mountpoint == "/":
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Cannot Mount root dataset.\n"
            }, exit_on_error=True)
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Dataset already mounted to {dataset_mountpoint}\n"
        }, exit_on_error=True)

    real_mountpoint = None
    if mountpoint:
        if len(mountpoint) > 1:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Boot environments can only view mounted to one location at once.\n"
            }, exit_on_error=True)
        real_mountpoint = mountpoint[0]

    zedenv_mount(boot_environment, real_mountpoint, verbose, be_root)
