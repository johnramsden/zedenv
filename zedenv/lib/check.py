"""
Startup checks
"""

import sys
import subprocess
import logging

import zedenv.lib.zfs.linux


def startup_check():
    system = check_system()
    if zfs_module_loaded() and zpool_exists():
        if system == "linux":
            root_dataset = zedenv.lib.zfs.linux.mount_dataset("/")
        else:
            raise RuntimeError(f"{system} is not yet supported by zedenv")

        if root_dataset is None:
            raise RuntimeError(
                "System is not booting off ZFS root dataset\n"
                "A ZFS root dataset is required for boot environments.")


def check_system():
    # TODO: Add proper system checks
    if True:
        return "linux"


def zfs_module_loaded():
    # Check 'zfs' module loaded
    with open("/proc/modules") as f:
        if "zfs" not in f.read():
            raise RuntimeError(
                "The ZFS module is not loaded.\n"
                "Load the ZFS module with 'modprobe zfs'")

    return True


def zpool_exists():
    try:
        subprocess.check_call(
            ["zpool", "get", "-H", "version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "No pool found, a zpool is required to use zedenv.\n")

    return True
