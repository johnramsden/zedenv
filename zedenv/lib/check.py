"""
Startup checks
"""

import sys
import subprocess


class ZECheck:
    def startup_check(self):
        if self.zfs_module_loaded() and self.zpool_exists():
            try:
                root_dataset = self.system_zfs_root()
            except OSError as e:
                sys.exit("ERROR: {}"
                         "\nSystem must be booting off a ZFS root dataset\n"
                         "to use boot environments".format(e))

            print("System booting from ZFS dataset: ", root_dataset)

    def zfs_module_loaded(self):
        # Check 'zfs' module loaded
        with open("/proc/modules") as f:
            if "zfs" not in f.read():
                sys.exit("The ZFS module is not loaded.\n"
                         "Load the ZFS module with 'modprobe zfs'")

        return True

    def zpool_exists(self):
        try:
            subprocess.check_call(
                ["zpool", "get", "-H", "version"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            sys.exit("No zpool found, a zpool is required to use zedenv.\n")

        return True

    def system_zfs_root(self):
        # Check if 'zfs' root
        root_dataset_mount = None
        with open("/proc/mounts") as f:
            for mount in f.read().splitlines():
                if "/ zfs" in mount:
                    root_dataset_mount = mount
                    break

        if root_dataset_mount is None:
            raise OSError("System doesn't boot from ZFS dataset")

        return root_dataset_mount.split(" ")[0]