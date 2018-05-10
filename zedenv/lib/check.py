"""
Startup checks
"""

import pyzfsutils.cmd


def startup_check_bootfs() -> list:
    """
    Checks if system is supported and has a bootfs set
    """
    bootfs_list = None
    try:
        bootfs_list = pyzfsutils.cmd.zpool_get(scripting=True,
                                               properties=["bootfs"],
                                               columns=["name", "value"])
    except RuntimeError as err:
        raise

    bootfs = [i.split() for i in bootfs_list.splitlines() if i.split()[1] != "-"]
    if not bootfs:
        raise RuntimeError("No bootfs has been set on zpool")

    return bootfs
