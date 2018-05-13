"""
Startup checks
"""

import pyzfsutils.cmd
import pyzfsutils.check
import pyzfsutils.system.agnostic


def bootfs_for_pool(zpool: str) -> str:
    bootfs_list = None
    try:
        bootfs_list = pyzfsutils.cmd.zpool_get(pool=zpool,
                                               scripting=True,
                                               properties=["bootfs"],
                                               columns=["value"])
    except RuntimeError as err:
        raise

    bootfs = [i.split()[0] for i in bootfs_list.splitlines() if i.split()[0] != "-"]
    if not bootfs:
        raise RuntimeError("No bootfs has been set on zpool")

    return bootfs[0]


def startup_check_bootfs(zpool: str) -> str:
    """
    Checks if system is supported and has a bootfs set
    Returns bootfs for specified pool
    """
    bootfs = None
    try:
        bootfs = bootfs_for_pool(zpool)
    except RuntimeError as err:
        raise

    return bootfs


def startup_check():
    try:
        pyzfsutils.check.is_root_on_zfs()
    except RuntimeError as err:
        raise RuntimeError(
            f"System is not booting off a ZFS root dataset.\n{err}\n")

    try:
        startup_check_bootfs(
            pyzfsutils.system.agnostic.mountpoint_dataset("/").split("/")[0])
    except RuntimeError as err:
        raise RuntimeError(f"Couldn't get bootfs property of pool.\n{err}\n")
