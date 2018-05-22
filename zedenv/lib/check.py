"""
Startup checks
"""

import pyzfscmds.check
import pyzfscmds.cmd
import pyzfscmds.system.agnostic

import zedenv.lib.be


def startup_check():
    try:
        pyzfscmds.check.is_root_on_zfs()
    except RuntimeError as err:
        raise RuntimeError(
            f"System is not booting off a ZFS root dataset.\n")

    try:
        zedenv.lib.be.bootfs_for_pool(
            pyzfscmds.system.agnostic.mountpoint_dataset("/").split("/")[0])
    except RuntimeError as err:
        raise RuntimeError(f"Couldn't get bootfs property of pool.\n{err}\n")
