import datetime
import subprocess
import platform
from contextlib import contextmanager
import datetime
from typing import List, Optional
import locale


@contextmanager
def setlocale(encoding: str="C"):
    """
    See: https://stackoverflow.com/a/24070673
    """
    saved = locale.setlocale(locale.LC_ALL)
    try:
        yield locale.setlocale(locale.LC_ALL, encoding)
    finally:
        locale.setlocale(locale.LC_ALL, saved)


def parse_time(origin_property: str, fmt: str="%Y-%m-%d-%H-%f",
               encoding: str="C", no_setlocale: bool=False) -> datetime:

    if no_setlocale:
        return datetime.datetime.strptime(origin_property, fmt)

    with setlocale(encoding=encoding):
        origin_datetime: datetime = datetime.datetime.strptime(origin_property, fmt)

    return origin_datetime


def mount(call_args: List[str] = None,
          mount_command: str = "mount"):

    mount_call = [mount_command]
    if call_args:
        mount_call.extend(call_args)

    try:
        mount_output = subprocess.check_output(
            mount_call, universal_newlines=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get mount data.\n{e}\n.")

    mount_list = mount_output.splitlines()

    return mount_list


def umount(target: str, call_args: List[str] = None):
    umount_args = []
    if call_args:
        umount_args.extend(call_args)

    umount_args.append(target)

    try:
        umount_output = mount(umount_args, mount_command="umount")
    except RuntimeError as e:
        raise RuntimeError(f"Failed to unmount {target}\n{e}\n.")

    return umount_output


def zfs_manual_mount(dataset: str, mountpoint: str, call_args: Optional[list] = None):
    system_platform = platform.system().lower()

    mount_call = ["-t", "zfs"]
    mount_call_fallback = ["-t", "zfs"]
    if system_platform == "linux":
        """
        Temp mount on linux requires '-o zfsutil', see:
        https://github.com/zfsonlinux/zfs/issues/7452
        """
        mount_call.extend(["-o", "zfsutil"])

    if call_args:
        mount_call.extend(call_args)
        mount_call_fallback.extend(call_args)

    mount_call.extend([dataset, mountpoint])
    mount_call_fallback.extend([dataset, mountpoint])

    try:
        mount(call_args=mount_call)
    except RuntimeError:
        if len(mount_call) != len(mount_call_fallback):
            try:
                # Using `-o zfsutil` fails if we want to mount a dataset that is already mounted
                mount(call_args=mount_call_fallback)
            except RuntimeError:
                raise
        else:
            raise
