"""
Functions for common boot environment tasks
"""

import datetime
import pyzfscmds.check
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility as zfs_utility
from typing import Optional, List, Dict

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


def bootfs_for_pool(zpool: str) -> str:
    bootfs_list = None
    try:
        bootfs_list = pyzfscmds.cmd.zpool_get(pool=zpool,
                                              scripting=True,
                                              properties=["bootfs"],
                                              columns=["value"])
    except RuntimeError as err:
        raise

    bootfs = [i.split()[0] for i in bootfs_list.splitlines() if i.split()[0] != "-"]
    if not bootfs:
        raise RuntimeError("No bootfs has been set on zpool")

    return bootfs[0]


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


def snapshot(boot_environment_name,
             boot_environment_root,
             snap_prefix: str = "ze",
             snap_suffix_time_format: str = "%Y-%m-%d-%H-%f") -> str:
    """
    Recursively Snapshot BE
    :param boot_environment_name: Name of BE to snapshot.
    :param boot_environment_root: Root dataset for BEs.
    :param snap_prefix: Prefix on snapshot names.
    :param snap_suffix_time_format: Suffix on snapshot names.
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

    suffix_time = datetime.datetime.now().strftime(snap_suffix_time_format)
    full_snap_suffix = f"{snap_prefix}-{suffix_time}"

    try:
        pyzfscmds.cmd.zfs_snapshot(dataset_name,
                                   full_snap_suffix,
                                   recursive=True)
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to create snapshot: '{dataset_name}@{full_snap_suffix}'"
        }, exit_on_error=True)

    return full_snap_suffix


def root(mount_dataset: str = "/") -> Optional[str]:
    """
    Root of boot environment datasets, e.g. zpool/ROOT
    """
    mountpoint_dataset = pyzfscmds.system.agnostic.mountpoint_dataset(mount_dataset)
    if mountpoint_dataset is None:
        return None

    return zfs_utility.dataset_parent(mountpoint_dataset)


def mount_pool(mount_dataset: str = "/") -> Optional[str]:
    mountpoint_dataset = pyzfscmds.system.agnostic.mountpoint_dataset(mount_dataset)
    if mountpoint_dataset is None:
        return None

    return mountpoint_dataset.split("/")[0]


def dataset_pool(dataset: str, zfs_type: str = 'filesystem') -> Optional[str]:
    if dataset is None or not pyzfscmds.utility.dataset_exists(dataset, zfs_type=zfs_type):
        return None

    return dataset.split("/")[0]


def is_current_boot_environment(boot_environment: str) -> bool:
    root_dataset = pyzfscmds.system.agnostic.mountpoint_dataset("/")

    be_root = root()
    if be_root is None or not (root_dataset == f"{be_root}/{boot_environment}"):
        return False

    return is_active_boot_environment(f"{be_root}/{boot_environment}",
                                      dataset_pool(f"{be_root}/{boot_environment}"))


def is_active_boot_environment(boot_environment_dataset: str, zpool: str) -> bool:
    return bootfs_for_pool(zpool) == boot_environment_dataset


def split_zfs_output(zfs_list: str) -> list:
    property_list = [line for line in zfs_list.splitlines()]
    return [line.split() for line in property_list]


def list_boot_environments(target: str, columns: list) -> List[Dict[str, str]]:
    """
    Returns a list of dictionaries with properties by name
    E.g.:
    [
        {
            'name': 'vault/ROOT/default-2@2018-05-21-161500',
            'creation': 'Mon-May-21-16:15-2018'
        }, ...
    ]

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

    split_property_list = split_zfs_output(list_output)

    # Get all properties except date, then add date converted to string
    full_property_list = []
    date_length = 5         # Num items from date in array

    # Put each property in dict, with creation time put in separately due to being split
    for line in split_property_list:
        if line[0] != target:
            line_item = {}
            line_date = "-".join(line[len(line) - date_length:])
            line_columns = line[:-date_length]

            for i, it in enumerate(line_columns):
                if columns[i] != 'creation':
                    line_item[columns[i]] = it

            line_item['creation'] = line_date

            full_property_list.append(line_item)

    return full_property_list
