"""Test zedenv get command"""

import pytest
import pyzfscmds.cmd
import pyzfscmds.utility

import zedenv.cli.get

require_root_dataset = pytest.mark.require_root_dataset
require_zfs_version = pytest.mark.require_zfs_version


@require_root_dataset
def test_boot_environment_get(root_dataset):
    test_prop = "org.zedenv:test"
    test_prop_val = "test"

    pyzfscmds.cmd.zfs_set(root_dataset, f"{test_prop}={test_prop_val}")

    assert f"{test_prop}\t{test_prop_val}" in zedenv.cli.get.zedenv_get(
        [test_prop], True, False, False, root_dataset)
