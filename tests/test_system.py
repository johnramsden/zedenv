import pytest

import zedenv.lib.system

require_root_dataset = pytest.mark.require_root_dataset
require_zpool_root_mountpoint = pytest.mark.require_zpool_root_mountpoint

"""zfs agnostic tests"""


def test_mount():
    zedenv.lib.system.mount()
