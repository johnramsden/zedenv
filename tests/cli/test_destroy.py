"""Test zedenv create command"""

import datetime

import pytest
import pyzfscmds.utility as zfs_utility

import zedenv.cli.destroy
import zedenv.cli.create
import zedenv.lib.check
import zedenv.cli.activate

require_root_dataset = pytest.mark.require_root_dataset
require_unsafe = pytest.mark.require_unsafe
require_zfs_version = pytest.mark.require_zfs_version
require_root_on_zfs = pytest.mark.require_root_on_zfs


@require_root_dataset
@pytest.fixture(scope="function")
def created_boot_environment(root_dataset):
    parent_dataset = zfs_utility.dataset_parent(root_dataset)

    boot_environment = f"zedenv-{datetime.datetime.now().isoformat()}"
    verbose = True
    existing = False

    zedenv.cli.create.zedenv_create(parent_dataset, root_dataset,
                                    boot_environment, verbose, existing)

    return boot_environment


@require_unsafe
@require_root_dataset
@require_zfs_version
def test_boot_environment_destroyed(root_dataset, created_boot_environment):
    parent_dataset = zfs_utility.dataset_parent(root_dataset)

    verbose = True
    unmount = False

    zedenv.cli.destroy.zedenv_destroy(created_boot_environment,
                                      parent_dataset,
                                      root_dataset,
                                      verbose,
                                      unmount)

    # assert not zfs_utility.dataset_exists(f"{parent_dataset}/{created_boot_environment}")


@require_unsafe
@require_root_dataset
@require_zfs_version
@require_root_on_zfs
def test_boot_environment_destroy_fails(root_dataset, created_boot_environment):
    """
    Wont fail if not root on ZFS
    """
    parent_dataset = zfs_utility.dataset_parent(root_dataset)

    verbose = True
    unmount = False

    zedenv.cli.activate.zedenv_activate(created_boot_environment,
                                        parent_dataset, verbose, None, False)

    with pytest.raises(SystemExit):
        zedenv.cli.destroy.zedenv_destroy(created_boot_environment,
                                          parent_dataset,
                                          root_dataset,
                                          verbose,
                                          unmount)
