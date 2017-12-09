"""zfs snapshot tests"""

import pytest
import datetime

from zedenv.lib.zfs.command import ZFS

require_root_dataset = pytest.mark.require_root_dataset


# Incorrect options to test
@pytest.mark.parametrize("snapname,properties", [
        (None, ["user_prop=on", "otheruser_prop=on"]),
        (f"@zedenv-test", ["user_prop=on", "otheruser_prop=on"]),
        ("", ["user_prop=on", "otheruser_prop=on"]),
        ("@", ["user_prop=on", "otheruser_prop=on"])
    ])
# Acceptable options
@pytest.mark.parametrize("recursive", [True, False])
@require_root_dataset
def test_zfs_snapshot_name_fails(root_dataset, snapname, recursive, properties):

    with pytest.raises((TypeError, RuntimeError)):
        ZFS.snapshot(root_dataset, snapname, recursive=recursive, properties=properties)


# Incorrect options to test
@pytest.mark.parametrize("properties", [
        ["mountpoint"], ["mountpoint=legacy"], "mountpoint=legacy"
    ])
# Acceptable options
@pytest.mark.parametrize("recursive", [True, False])
@require_root_dataset
def test_zfs_snapshot_property_fails(root_dataset, recursive, properties):
    snapname = f"@zedenv-{datetime.datetime.now().isoformat()}"
    with pytest.raises(RuntimeError):
        ZFS.snapshot(root_dataset, snapname, recursive=recursive, properties=properties)


def test_zfs_snapshot_nonexistant_dataset_fails():
    with pytest.raises(RuntimeError):
        ZFS.snapshot("nonexistantdataset", f"@zedenv-{datetime.datetime.now().isoformat()}")


@pytest.mark.parametrize("recursive", [True, False])
@pytest.mark.parametrize("properties", [None, ["zedenv:user_prop=on", "zedenv:otheruser_prop=on"]])
@require_root_dataset
def test_zfs_snapshot_successful(root_dataset, recursive, properties):
    snapname = f"zedenv-{datetime.datetime.now().isoformat()}"
    """ Test will pass if snapshot successful"""
    ZFS.snapshot(root_dataset, snapname, recursive=recursive, properties=properties)
