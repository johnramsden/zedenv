"""Test zedenv create command"""

import datetime

import pytest
import pyzfscmds.utility as zfs_utility

import zedenv.cli.create
import zedenv.cli.list

require_zfs_version = pytest.mark.require_zfs_version
require_root_dataset = pytest.mark.require_root_dataset


@require_zfs_version
@require_root_dataset
def test_boot_environment_listed(root_dataset, capsys):
    parent_dataset = zfs_utility.dataset_parent(root_dataset)

    boot_environment = f"zedenv-{datetime.datetime.now().isoformat()}"

    verbose = True
    existing = None

    columns = ["name", "origin", "creation"]

    zedenv.cli.create.zedenv_create(parent_dataset, root_dataset,
                                    boot_environment, verbose, existing, None)

    be_list = zedenv.cli.list.configure_boot_environment_list(
        zfs_utility.dataset_parent(root_dataset), columns, True)

    assert any(f"{boot_environment}" in s for s in be_list)
