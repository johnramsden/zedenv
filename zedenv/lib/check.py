"""
Startup checks
"""

import sys
import subprocess
import logging

import zedenv.lib.zfs.linux


class ZECheck:
    def __init__(self, system="linux"):
        self.system = system

    def startup_check(self):
        if self.zfs_module_loaded() and self.zpool_exists():
            if self.system == "linux":
                root_dataset = zedenv.lib.zfs.linux.mount_dataset("/")
            else:
                raise RuntimeError(f"{self.system} is not yet supported by zedenv")

            if root_dataset is None:
                raise RuntimeError(
                    "System is not booting off ZFS root dataset\n"
                    "A ZFS root dataset is required for boot environments.")

    def zfs_module_loaded(self):
        # Check 'zfs' module loaded
        with open("/proc/modules") as f:
            if "zfs" not in f.read():
                raise RuntimeError(
                    "The ZFS module is not loaded.\n"
                    "Load the ZFS module with 'modprobe zfs'")

        return True

    def zpool_exists(self):
        try:
            subprocess.check_call(
                ["zpool", "get", "-H", "version"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "No pool found, a zpool is required to use zedenv.\n")

        return True
