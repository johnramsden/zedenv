import pytest

import zedenv.lib.zfs.utility as zfs_utility
from zedenv.lib.zfs.command import ZFS

"""zfs utilities tests"""

"""Test variables"""
be_dataset_root = "zpool/ROOT"
root_be_name = "default"
root_dataset = f"{be_dataset_root}/{root_be_name}"


def test_zfs_is_snapshot():
    assert zfs_utility.is_snapshot(f"{root_dataset}@my-snap")


def test_dataset_parent():
    assert zfs_utility.dataset_parent(root_dataset) == be_dataset_root


def test_dataset_child_name():
    assert zfs_utility.dataset_child_name(root_dataset) == root_be_name


def test_snapshot_parent_dataset():
    assert zfs_utility.snapshot_parent_dataset(f"{root_dataset}@my-snap") == root_dataset


"""zfs commands tests"""


def test_dataset_exists():
    with pytest.raises(RuntimeError):
        ZFS.list("nonexistantdataset")
