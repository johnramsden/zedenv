import zedenv

import subprocess
import sys

def test_zfs_module_loaded():
    assert zedenv.zfs_module_loaded()

def test_zpool_exists():
    assert zedenv.zpool_exists()