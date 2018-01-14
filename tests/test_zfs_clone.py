import pytest
import datetime

import zedenv.lib.zfs.utility as zfs_utility
from zedenv.lib.zfs.command import ZFS

"""zfs commands tests"""

require_root_dataset = pytest.mark.require_root_dataset


def create_clone(root_dataset, snapname, properties: list=None, create_parent=False):
    clone_root = zfs_utility.dataset_parent(root_dataset)
    clone_suffix = f"zedenv-{datetime.datetime.now().isoformat()}"
    try:
        ZFS.snapshot(root_dataset, snapname)
        ZFS.clone(f"{root_dataset}@{snapname}",
                  f"{clone_root}/{clone_suffix}",
                  properties=properties,
                  create_parent=create_parent)
    except (RuntimeError, TypeError):
        raise


@pytest.mark.parametrize("properties", [None, [], ["compression=off"]])
@pytest.mark.parametrize("create_parent", [True, False])
@require_root_dataset
def test_zfs_clone_successful(root_dataset, properties, create_parent):
    # Cannot parameterize, must be unique
    snapname = f"zedenv-{datetime.datetime.now().isoformat()}"
    print(f"Creating {root_dataset}@{snapname}")
    """ Test will pass if clone successful"""
    create_clone(root_dataset, snapname,
                 properties=properties, create_parent=create_parent)


@pytest.mark.parametrize("snapname", [
        None, f"@zedenv-test", "", "@"
    ])
@pytest.mark.parametrize("properties", [None, [], ["compression=off"]])
@pytest.mark.parametrize("create_parent", [True, False])
@require_root_dataset
def test_zfs_clone_fails(root_dataset, snapname, properties, create_parent):
    print(f"Creating {root_dataset}@{snapname}")
    """ Test will pass if clone fails"""

    with pytest.raises((TypeError, RuntimeError)):
        create_clone(root_dataset, snapname, properties=properties, create_parent=create_parent)
