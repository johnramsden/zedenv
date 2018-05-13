"""Test zedenv create command"""

import pytest

import zedenv.cli.activate

require_root_dataset = pytest.mark.require_root_dataset


@require_root_dataset
def test_boot_environment_activated(root_dataset):
    """
    Will end up returning false since root dataset is not a ZFS dataset
    """
    verbose = True

    zedenv.cli.activate.zedenv_activate(root_dataset, verbose, "systemdboot", False)
