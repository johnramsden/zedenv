"""
Functions for common boot environment tasks
"""

from zedenv.lib.zfs.command import ZFS
import zedenv.lib.zfs.utility as zfs_utility
import zedenv.lib.zfs.linux as zfs_linux

from zedenv.lib.logger import ZELogger


def get_root():
    return zfs_utility.dataset_parent(zfs_linux.mount_dataset("/"))


def get_full_dataset(name):
    return f"{get_root()}/{name}"


def list_boot_environments(target) -> list:
    """
    zfs list -H -t filesystem,snapshot,volume \
    -s creation \
    -o name,used,usedds,usedbysnapshots,usedrefreserv,refer,creation,origin \
    -r
    """

    """
        def list(cls, target, recursive=False, depth=None, scripting=True,
             parsable=False, columns: list = None, zfs_types: list = None,
             sort_properties_ascending: list = None, sort_properties_descending: list = None):
    """
    try:
        list_output = ZFS.list(target, recursive=True,
                               zfs_types=["filesystem", "snapshot", "volume"],
                               sort_properties_ascending=["creation"],
                               columns=["name", "used", "usedds",
                                        "usedbysnapshots", "usedrefreserv",
                                        "refer", "creation", "origin"])
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION", "message": f"Failed to get properties of '{target}'"
        }, exit_on_error=True)

    """
    Take each line of output containing properties and convert
    it to a list of property=value strings
    """
    property_list = [line for line in list_output.splitlines()]

    return property_list
