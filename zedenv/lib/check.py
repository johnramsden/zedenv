"""
Startup checks
"""

import pyzfsutils.cmd
import pyzfsutils.check
import zedenv.lib.boot_environment as be


def startup_check_bootfs(zpool: str) -> list:
    """
    Checks if system is supported and has a bootfs set
    """
    bootfs_list = None
    try:
        bootfs_list = pyzfsutils.cmd.zpool_get(pool=zpool,
                                               scripting=True,
                                               properties=["bootfs"],
                                               columns=["name", "value"])
    except RuntimeError as err:
        raise

    bootfs = [i.split() for i in bootfs_list.splitlines() if i.split()[1] != "-"]
    if not bootfs:
        raise RuntimeError("No bootfs has been set on zpool")

    return bootfs


def startup_check():
    try:
        pyzfsutils.check.is_root_on_zfs()
    except RuntimeError as err:
        raise RuntimeError(
            f"System is not booting off a ZFS root dataset.\n{err}\n")

    try:
        startup_check_bootfs(be.pool())
    except RuntimeError as err:
        raise RuntimeError(f"Couldn't get bootfs property of pool.\n{err}\n")
