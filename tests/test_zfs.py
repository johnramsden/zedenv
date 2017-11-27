import pytest
import datetime

import zedenv.lib.zfs.utility as zfs_utility
from zedenv.lib.zfs.command import ZFS

"""zfs utilities tests"""

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


"""zfs commands tests"""

require_root_dataset = pytest.mark.require_root_dataset


def test_zfs_list_fails():
    with pytest.raises(RuntimeError):
        ZFS.list("nonexistantdataset")

"""
It's not currently possible to access fixtures inside parameterized fixtures, 
therefore root data set cannot be accessed directly inside a parameterize fixture. 

See: https://github.com/pytest-dev/pytest/issues/349 
"""


@pytest.mark.parametrize(
    "snapname,properties,create_parent", [
        (f"zedenv-{datetime.datetime.now().isoformat()}", None, False),
        (f"zedenv-{datetime.datetime.now().isoformat()}", ["compression=off"], False),
        (f"zedenv-{datetime.datetime.now().isoformat()}", ["compression=off"], True),
        (f"zedenv-{datetime.datetime.now().isoformat()}", [], True),
        (f"zedenv-{datetime.datetime.now().isoformat()}", [], False),
    ])
@require_root_dataset
def test_zfs_clone_successful(root_dataset, snapname, properties, create_parent):
    print(f"Creating {root_dataset}@{snapname}")
    """ Test will pass if clone successful"""
    ZFS.snapshot(root_dataset, snapname)
    ZFS.clone(f"{root_dataset}@{snapname}",
              f"{zfs_utility.dataset_parent(root_dataset)}/zedenv-{datetime.datetime.now().isoformat()}",
              properties=properties,
              create_parent=create_parent)

# @pytest.mark.parametrize(
#     "snapname,properties,create_parent", [
#         (f"@zedenv-{datetime.datetime.now().isoformat()}", None, False),
#         (f"", ["compression=off"], False),
#         (f"zedenv-{datetime.datetime.now().isoformat()}", ["compression=off"], True),
#         (f"zedenv-{datetime.datetime.now().isoformat()}", [], True),
#         (f"zedenv-{datetime.datetime.now().isoformat()}", [], False),
# ])
# @require_root_dataset
# def test_zfs_clone_fails(root_dataset):
#     with pytest.raises(RuntimeError):
#         ZFS.clone(f"{root_dataset}@fakesnap", "nonexistantdataset")


# def test_zfs_get_fails():
#     with pytest.raises(RuntimeError):
#         ZFS.get("nonexistantdataset")
#
# @require_root_dataset
# def test_zfs_get_successful(root_dataset):
#     """ Test will pass if get successful"""
#     ZFS.get(root_dataset)
#
# @require_root_dataset
# def test_zfs_list_successful(root_dataset):
#     """ Test will pass if list successful"""
#     ZFS.list(root_dataset)
#
# def test_zfs_snapshot_fails():
#     with pytest.raises(RuntimeError):
#         ZFS.snapshot("nonexistantdataset")
#
# @require_root_dataset
# def test_zfs_snapshot_successful(root_dataset):
#     """ Test will pass if snapshot successful"""
#     ZFS.snapshot(root_dataset)root_dataset
#
#
#
