"""Test zedenv set command"""

import pytest
import pyzfscmds.cmd
import pyzfscmds.utility

import zedenv.cli.set

require_root_dataset = pytest.mark.require_root_dataset
require_zfs_version = pytest.mark.require_zfs_version


@require_root_dataset
def test_boot_environment_activated(root_dataset):
    test_prop = "org.zedenv:test"
    test_prop_val = "test"

    zedenv.cli.set.zedenv_set(True, [f"{test_prop}={test_prop_val}"], root_dataset)

    assert (test_prop and test_prop_val) in pyzfscmds.cmd.zfs_get(root_dataset,
                                                                  properties=[test_prop],
                                                                  columns=['property',
                                                                           'value']).split()
