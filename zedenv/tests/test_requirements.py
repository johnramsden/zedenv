import zedenv

import subprocess
import sys

def test_zfs_module_loaded():
    with open("/proc/modules") as f:
        assert "zfs" in f.read()