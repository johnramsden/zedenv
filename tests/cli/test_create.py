"""Test zedenv create command"""

import datetime

import pytest
import pyzfscmds.utility as zfs_utility

import zedenv.cli.create
import zedenv.lib.check

require_root_dataset = pytest.mark.require_root_dataset
require_zfs_version = pytest.mark.require_zfs_version


@require_zfs_version
@require_root_dataset
def test_boot_environment_created(root_dataset):
    parent_dataset = zfs_utility.dataset_parent(root_dataset)

    boot_environment = f"zedenv-{datetime.datetime.now().isoformat()}"
    verbose = True
    existing = None

    zedenv.cli.create.zedenv_create(parent_dataset, root_dataset,
                                    boot_environment, verbose, existing, None)

    assert zfs_utility.dataset_exists(f"{parent_dataset}/{boot_environment}")


@require_zfs_version
@require_root_dataset
def test_same_boot_environment_created(root_dataset):
    parent_dataset = zfs_utility.dataset_parent(root_dataset)

    boot_environment = f"zedenv-{datetime.datetime.now().isoformat()}"
    verbose = True
    existing = None

    zedenv.cli.create.zedenv_create(parent_dataset, root_dataset,
                                    boot_environment, verbose, existing, None)
    with pytest.raises(SystemExit):
        zedenv.cli.create.zedenv_create(parent_dataset, root_dataset,
                                        boot_environment, verbose, existing, None)
