"""Test zedenv create command"""

import datetime

import pytest

import zedenv.lib.check
import zedenv.lib.zfs.utility as zfs_utility
from zedenv.lib.zfs.command import ZFS

import zedenv.cli.create

require_root_dataset = pytest.mark.require_root_dataset


def test_zfs_module_loaded():
    assert zedenv.lib.check.zfs_module_loaded()


@require_root_dataset
def test_boot_environment_created(root_dataset):
    parent_dataset = zfs_utility.dataset_parent(root_dataset)

    boot_environment = f"zedenv-{datetime.datetime.now().isoformat()}"
    verbose = True
    existing = False

    zedenv.cli.create.zedenv_create(parent_dataset, root_dataset,
                                    boot_environment, verbose, existing)

    assert zfs_utility.dataset_exists(f"{parent_dataset}/{boot_environment}") is True
