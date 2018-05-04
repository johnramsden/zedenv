"""
Startup checks
"""

import pyzfsutils.check


def startup_check():
    """
    Checks if system is supported and root is on ZFS
    """
    try:
        pyzfsutils.check.is_root_on_zfs()
    except RuntimeError as err:
        raise err
