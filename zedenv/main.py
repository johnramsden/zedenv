"""
zedenv boot environment manager cli
"""

import signal
import subprocess
import sys

from click import core
import zedenv
import zedenv.lib.check as ze_check

signal.signal(signal.SIGINT, signal.default_int_handler)


def cli():
    """ZFS boot environment manager cli"""
    print("zedenv cli ", zedenv.__version__)

    ze_check.ZECheck().startup_check()


if __name__ == '__main__':
    cli()