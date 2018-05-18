"""
Functions for common boot environment tasks
"""

import datetime
import pyzfscmds.check
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility as zfs_utility
from typing import Optional

import zedenv.lib.check
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
        used = pyzfscmds.cmd.zfs_get(boot_environment,
                       properties=["used"],
                       columns=["value"])

    return 1
"""


def properties(dataset, appended_properties: Optional[list]) -> list:
    dataset_properties = None
    try:
        dataset_properties = pyzfscmds.cmd.zfs_get(dataset,
                                                   columns=["property", "value"],
                                                   source=["local", "received"],
                                                   properties=["all"])
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to get properties of '{dataset}'"
        }, exit_on_error=True)

    """
    Take each line of output containing properties and convert
    it to a list of property=value strings
    """
    dp = [line.split() for line in dataset_properties.splitlines()]
    remove_props = [rp[0] for rp in appended_properties]
    used_props = ["=".join(p) for p in dp if p[0] not in remove_props]

    used_props.extend(["=".join(pa) for pa in appended_properties])

    return used_props


def snapshot(boot_environment_name, boot_environment_root, snap_prefix="zedenv"):
    """
    Recursively Snapshot BE
    :param boot_environment_name: Name of BE to snapshot.
    :param boot_environment_root: Root dataset for BEs.
    :param snap_prefix: Prefix on snapshot names.
    :return: Name of snapshot without dataset.
    """
    if "/" in boot_environment_name:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": ("Failed to get snapshot.\n",
                        "Existing boot environment name ",
                        f"{boot_environment_name} should not contain '/'")
        }, exit_on_error=True)

    dataset_name = f"{boot_environment_root}/{boot_environment_name}"

    snap_suffix = datetime.datetime.now().strftime('ze-%Y-%m-%d-%H-%f')

    try:
        pyzfscmds.cmd.zfs_snapshot(dataset_name,
                                   snap_suffix,
                                   recursive=True)
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to create snapshot: '{dataset_name}@{snap_suffix}'"
        }, exit_on_error=True)

    return snap_suffix


def root(mount_dataset: str = "/") -> Optional[str]:
    """
    Root of boot environment datasets, e.g. zpool/ROOT
    """
    mountpoint_dataset = pyzfscmds.system.agnostic.mountpoint_dataset(mount_dataset)
    if mountpoint_dataset is None:
        return None

    return zfs_utility.dataset_parent(mountpoint_dataset)


def pool(mount_dataset: str = "/") -> Optional[str]:
    mountpoint_dataset = pyzfscmds.system.agnostic.mountpoint_dataset(mount_dataset)
    if mountpoint_dataset is None:
        return None

    return mountpoint_dataset.split("/")[0]


def dataset_pool(dataset: str) -> Optional[str]:
    return dataset.split("/")[0] if dataset is not None else None


def is_current_boot_environment(boot_environment: str) -> bool:
    root_dataset = pyzfscmds.system.agnostic.mountpoint_dataset("/")

    be_root = root()
    if be_root is None or not (root_dataset == "/".join([be_root, boot_environment])):
        return False

    return zedenv.lib.check.startup_check_bootfs(pool()) == root_dataset


def list_boot_environments(target: str, columns: list) -> list:
    """
    TODO:
    Space Used:
    By Snapshot = used
    By Other:
        Space = usedds + usedrefreserv
          If all prior BE destroyed (full space):
            Space += usedbysnapshots
    """
    list_output = None
    try:
        list_output = pyzfscmds.cmd.zfs_list(target, recursive=True,
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

    property_list = [line for line in list_output.splitlines()]
    split_property_list = [line.split() for line in property_list]

    # Get all properties except date, then add date converted to string
    date_items = 5
    full_property_list = list()
    for line in split_property_list:
        if line[0] != target:
            # Get all properties except date
            formatted_property_line = line[:len(line) - date_items]

            # Add date converted to string
            formatted_property_line.append("-".join(line[-date_items:]))
            full_property_list.append(formatted_property_line)

    return full_property_list
