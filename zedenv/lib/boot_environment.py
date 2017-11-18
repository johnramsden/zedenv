"""
Functions for common boot environment tasks
"""

import zedenv.lib.zfs.command as zfs_command
import zedenv.lib.zfs.utility as zfs_utility
import zedenv.lib.zfs.linux as zfs_linux

from zedenv.lib.logger import ZELogger


def get_root():
    return zfs_utility.dataset_parent(zfs_linux.mount_dataset("/"))


def get_full_dataset(name):
    return f"{get_root()}/{name}"

def list_boot_environments() -> list:
    """
    zfs list -H -t filesystem,snapshot,volume \
    -s creation \
    -o name,used,usedds,usedbysnapshots,usedrefreserv,refer,creation,origin \
    -r
    """
    nothing = ""
    #zfs_command.list()
