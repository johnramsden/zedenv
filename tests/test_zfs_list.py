import pytest
import datetime

import zedenv.lib.zfs.utility as zfs_utility
from zedenv.lib.zfs.command import ZFS


"""zfs commands tests"""

require_root_dataset = pytest.mark.require_root_dataset


def test_zfs_list_fails():
    with pytest.raises(RuntimeError):
        ZFS.list("nonexistantdataset")


@require_root_dataset
def test_zfs_list_successful(root_dataset):
    """ Test will pass if list successful"""
    ZFS.list(root_dataset)