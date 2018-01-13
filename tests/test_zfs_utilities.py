"""zfs utilities tests"""

import pytest
import datetime

import zedenv.lib.zfs.utility as zfs_utility
from zedenv.lib.zfs.command import ZFS

require_root_dataset = pytest.mark.require_root_dataset

"""Test variables"""

test_dataset_names = {
    "boot_environment_root": "zpool/ROOT",
    "boot_environment":      "default",
    "root":                 "zpool/ROOT/default"
}


"""
Tests for function: zedenv.lib.zfs.utility.is_snapshot()
"""


# TODO: Finish
@pytest.mark.parametrize("snapname", [
    "", "@", "fakename/dataset"
    ])
def test_is_not_snapshot(snapname):
    assert zfs_utility.is_snapshot(snapname) is False


@require_root_dataset
def test_is_snapshot(root_dataset):
    snapname = f"zedenv-{datetime.datetime.now().isoformat()}"
    """ Test will pass if snapshot successful"""
    ZFS.snapshot(root_dataset, snapname)

    assert zfs_utility.is_snapshot(f"{root_dataset}@{snapname}")


"""
Tests for function: zedenv.lib.zfs.utility.is_clone()
"""


@require_root_dataset
def test_is_not_clone_valid_option(root_dataset):
    """Make sure valid ZFS options give 'False' if they're not a clone."""
    snapname = f"zedenv-{datetime.datetime.now().isoformat()}"
    """ Test will pass if snapshot successful"""
    ZFS.snapshot(root_dataset, snapname)

    try:
        dataset_is_clone = zfs_utility.is_clone(f"{root_dataset}@{snapname}")
        print(dataset_is_clone)
    except RuntimeError:
        raise

    assert not dataset_is_clone


@pytest.mark.parametrize("clonename", ["", "@", "fakename/dataset"])
def test_is_not_clone_invalid_option(clonename):
    """Make sure invalid ZFS options raise a RuntimeError."""
    with pytest.raises(RuntimeError):
        zfs_utility.is_clone(clonename)


@require_root_dataset
def test_is_clone(root_dataset):
    snapname = f"zedenv-{datetime.datetime.now().isoformat()}"
    ZFS.snapshot(root_dataset, snapname)

    clonename = f"{zfs_utility.dataset_parent(root_dataset)}/zedenv-{datetime.datetime.now().isoformat()}"
    ZFS.clone(f"{root_dataset}@{snapname}", clonename)

    print(clonename)

    assert zfs_utility.is_clone(clonename)


"""
Tests for function: zedenv.lib.zfs.utility.dataset_parent()
"""


def test_dataset_parent():
    assert zfs_utility.dataset_parent(test_dataset_names['root']) == test_dataset_names['boot_environment_root']


"""
Tests for function: zedenv.lib.zfs.utility.dataset_child_name()
"""


def test_dataset_child_name():
    assert zfs_utility.dataset_child_name(test_dataset_names['root']) == test_dataset_names['boot_environment']


"""
Tests for function: zedenv.lib.zfs.utility.parent_dataset()
"""


def test_snapshot_parent_dataset():
    assert zfs_utility.snapshot_parent_dataset(f"{test_dataset_names['root']}@my-snap") == test_dataset_names['root']