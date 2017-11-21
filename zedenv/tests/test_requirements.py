import zedenv.lib.check

import subprocess
import sys


def test_zfs_module_loaded():
    assert zedenv.lib.check.zfs_module_loaded()


def test_zpool_exists():
    assert zedenv.lib.check.zpool_exists()
