"""
Startup checks
"""

import pyzfscmds.check
import pyzfscmds.cmd
import pyzfscmds.system.agnostic

import zedenv.lib.be
from zedenv.lib.logger import ZELogger

import os
import sys
import errno


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


class Pidfile:

    """
    Reference:
    https://stackoverflow.com/a/23837022
    """

    def __init__(self, name="zedenv.pid", directory="/var/run"):
        self.pidfile = os.path.join(directory, name)

    def __enter__(self):
        if os.path.exists(self.pidfile):

            pid = None
            with open(self.pidfile) as f:
                pid = self._check()
                if pid:
                    self.pidfd = None
                    raise ProcessRunningException(
                        f'process already running in {self.pidfile} as {pid}')
                else:
                    os.remove(self.pidfile)

            if pid:
                ProcessRunningException(
                    f'process already running in {self.pidfile} as {pid}')

        try:
            with open(self.pidfile, 'w+') as f:
                f.write(str(os.getpid()))
        except OSError as e:
            ZELogger.log({
                "level": "EXCEPTION", "message": f"Cannot write to pidfile {self.pidfile}"
            }, exit_on_error=True)

        return self

    def __exit__(self, t, e, tb):
        # return false to raise, true to pass
        if t is None:
            # normal condition, no exception
            self._remove()
            return True
        elif isinstance(t, ProcessRunningException):
            # do not remove the other process lockfile
            return False
        else:
            # other exception
            if self.pidfd:
                # this was our lockfile, removing
                self._remove()
            return False

    def _remove(self):
        # removed pidfile
        os.remove(self.pidfile)

    def _check(self):
        """check if a process is still running
        the process id is expected to be in pidfile, which should exist.
        if it is still running, returns the pid, if not, return False."""

        try:
            with open(self.pidfile, 'r') as f:
                try:
                    pidstr = f.read()
                    pid = int(pidstr)
                except ValueError:
                    # not an integer
                    return False
                try:
                    os.kill(pid, 0)
                except OSError:
                    # can't deliver signal to pid
                    return False
                else:
                    return pid
        except FileNotFoundError:
            return False


class ProcessRunningException(BaseException):
    pass
