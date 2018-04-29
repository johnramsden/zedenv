"""
Functions for common boot environment tasks
"""

import pyzfsutils.lib.zfs.linux as zfs_linux
import pyzfsutils.lib.zfs.utility as zfs_utility
from pyzfsutils.lib.zfs.command import ZFS

from zedenv.lib.logger import ZELogger


"""
# TODO: Normalize based on size suffix.
def normalize(value):
    normalized = 1
    return normalized
"""

"""
# TODO: Write function to get size
def size(boot_environment) -> int:
    # Space calculation:
    # https://github.com/vermaden/beadm/blob/
    # 60f8d4de7b0a0a59360f631816d36cfefcc86b75/beadm#L389-L421

    if not zfs_utility.is_clone(boot_environment):
        used = ZFS.get(boot_environment,
                       properties=["used"],
                       columns=["value"])

    return 1
"""


def root(mount_dataset="/"):
    return zfs_utility.dataset_parent(zfs_linux.mount_dataset(mount_dataset))


def list_boot_environments(target, columns: list) -> list:
    """
    TODO:
    Space Used:
    By Snapshot = used
    By Other:
        Space = usedds + usedrefreserv
          If all prior BE destroyed (full space):
            Space += usedbysnapshots
    """
    try:
        list_output = ZFS.list(target, recursive=True,
                               zfs_types=["filesystem", "snapshot", "volume"],
                               sort_properties_ascending=["creation"],
                               columns=columns)
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION", "message": f"Failed to get properties of '{target}'"
        }, exit_on_error=True)

    """
    Take each line of output containing properties and convert
    it to a list of property=value strings
    """
    # noinspection PyUnboundLocalVariable
    property_list = [line for line in list_output.splitlines()]
    split_property_list = [line.split() for line in property_list]

    # Get all properties except date, then add date converted to string
    date_items = 5
    full_property_list = list()
    for line in split_property_list:
        if line[0] != target:
            # Get all properties except date
            formatted_property_line = line[:len(line)-date_items]

            # Add date converted to string
            formatted_property_line.append("-".join(line[-date_items:]))
            full_property_list.append(formatted_property_line)

    return full_property_list
