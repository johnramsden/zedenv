"""List boot environments cli"""

import os
import tempfile
import platform

from typing import Optional

import click
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility as zfs_utility

import zedenv.lib.be
import zedenv.lib.check
import zedenv.lib.system
from zedenv.lib.logger import ZELogger


def zedenv_mount(boot_environment: str, mountpoint: Optional[str], verbose: bool, be_root: str):
    """
    Create a temporary directory and mount a boot environment.
    If an extra argument is given, mount the boot environment at the given mountpoint.
    """

    system_platform = platform.system().lower()

    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Mounting boot environment '{boot_environment}'.\n"
    }, verbose)

    if not mountpoint:
        mountpoint_used = tempfile.mkdtemp(suffix=f"-{boot_environment}", prefix="zedenv-")
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"No mountpoint given, using a temporary directory {mountpoint_used}.\n"
        }, verbose)
    else:
        mountpoint_used = mountpoint[0]
        if os.path.ismount(mountpoint_used):
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"There is already a file system mounted at {mountpoint_used}"
            }, exit_on_error=True)

        if not os.path.isdir(mountpoint_used):
            ZELogger.log({
                "level": "EXCEPTION",
                "message": (f"The path'{mountpoint_used}' is not a directory, "
                            "cannot be used as mountpoint.\n")
            }, exit_on_error=True)
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Mountpoint '{mountpoint_used}' given, using as mountpoint.\n"
        }, verbose)

    be_dataset = f"{be_root}/{boot_environment}"

    mount_call = ["-t", "zfs"]
    if system_platform == "linux":
        """
        Temp mount on linux requires '-o zfsutil', see:
        https://github.com/zfsonlinux/zfs/issues/7452
        """
        mount_call.extend(["-o", "defaults,zfsutil"])

    mount_call.extend([be_dataset, mountpoint_used])

    try:
        zedenv.lib.system.mount(call_args=mount_call)
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed mounting data set to '{mountpoint_used}'.\n{e}"
        }, exit_on_error=True)

    ZELogger.verbose_log(
        {"level": "INFO", "message": f"Mounted data set to '{mountpoint_used}'.\n"}, verbose)
    if not verbose:
        ZELogger.log({"level": "INFO", "message": mountpoint_used})


@click.command(name="mount",
               help="Mount a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.argument('boot_environment')
@click.argument('mountpoint', nargs=-1, required=False)
def cli(boot_environment, mountpoint, verbose):
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

    zedenv_mount(boot_environment, mountpoint, verbose, be_root)
