"""Test zedenv create command"""

import datetime
import pytest
import pyzfscmds.utility as zfs_utility
import zedenv.cli.activate
import zedenv.cli.create
import zedenv.cli.destroy
import zedenv.lib.check

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
    existing = None
    zedenv.cli.create.zedenv_create(parent_dataset, root_dataset,
                                    boot_environment, verbose, existing, None)

    return boot_environment


@require_unsafe
@require_root_dataset
@require_zfs_version
def test_boot_environment_destroyed(root_dataset, created_boot_environment):
    parent_dataset = zfs_utility.dataset_parent(root_dataset)

    verbose = True
    noconfirm = True
    noop = True
    bootloader = None

    zedenv.cli.destroy.zedenv_destroy(created_boot_environment,
                                      parent_dataset,
                                      root_dataset,
                                      bootloader,
                                      verbose,
                                      noconfirm,
                                      noop)

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
    noconfirm = True
    noop = True
    bootloader = None

    zedenv.cli.activate.zedenv_activate(created_boot_environment,
                                        parent_dataset, verbose, bootloader, noconfirm, noop)

    with pytest.raises(SystemExit):
        zedenv.cli.destroy.zedenv_destroy(created_boot_environment,
                                          parent_dataset,
                                          root_dataset,
                                          bootloader,
                                          verbose,
                                          noconfirm,
                                          noop)
