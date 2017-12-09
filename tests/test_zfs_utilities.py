"""zfs utilities tests"""

import zedenv.lib.zfs.utility as zfs_utility

"""Test variables"""

test_dataset_names = {
    "boot_environment_root": "zpool/ROOT",
    "boot_environment":      "default",
    "root":                 "zpool/ROOT/default"
}


def test_zfs_is_snapshot():
    assert zfs_utility.is_snapshot(f"{test_dataset_names['root']}@my-snap")


def test_dataset_parent():
    assert zfs_utility.dataset_parent(test_dataset_names['root']) == test_dataset_names['boot_environment_root']


def test_dataset_child_name():
    assert zfs_utility.dataset_child_name(test_dataset_names['root']) == test_dataset_names['boot_environment']


def test_snapshot_parent_dataset():
    assert zfs_utility.snapshot_parent_dataset(f"{test_dataset_names['root']}@my-snap") == test_dataset_names['root']