"""Test zedenv setup"""

import pytest
import pyzfsutils.cmd

import zedenv.main

from click.testing import CliRunner

require_zpool = pytest.mark.require_zpool
require_root_dataset = pytest.mark.require_root_dataset


@require_zpool
@require_root_dataset
@pytest.fixture(scope="function")
def set_bootfs_failure(request, zpool, root_dataset):
    print("bootfs setup:")
    pyzfsutils.cmd.zpool_set(zpool, 'bootfs=')

    def fin():
        print("Re-set bootfs teardown")
        pyzfsutils.cmd.zpool_set(zpool, f'bootfs={root_dataset}')

    request.addfinalizer(fin)
    return set_bootfs_failure


@require_zpool
@require_root_dataset
def test_boot_no_bootfs(root_dataset, zpool, set_bootfs_failure):
    runner = CliRunner()
    result = runner.invoke(zedenv.main.cli, ['list'])
    assert not result.exit_code == 0
    assert result.exception
