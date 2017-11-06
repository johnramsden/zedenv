"""
zedenv boot environment manager cli
"""

import signal
import subprocess
import sys

from click import core
from zedenv import __version__

signal.signal(signal.SIGINT, signal.default_int_handler)


def zfs_module_loaded():
    # Check 'zfs' module loaded
    with open("/proc/modules") as f:
        if "zfs" not in f.read():
            sys.exit("The ZFS module is not loaded.\n"
                     "Load the ZFS module with 'modprobe zfs'")

    return True


def zpool_exists():
    try:
        subprocess.check_call(
            ["zpool", "get", "-H", "version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        sys.exit("No zpool found, a zpool is required to use zedenv.\n")

    return True


def system_zfs_root():
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


def cli():
    """ZFS boot environment manager cli"""
    print("zedenv cli ", __version__)

    if zfs_module_loaded() and zpool_exists():
        try:
            root_dataset = system_zfs_root()
        except OSError as e:
            sys.exit("ERROR: {}"
                     "\nSystem must be booting off a ZFS root dataset\n"
                     "to use boot environments".format(e))

        print("System booting from ZFS dataset: ", root_dataset)


if __name__ == '__main__':
    cli()