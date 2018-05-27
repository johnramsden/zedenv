import subprocess
import platform
from typing import List, Optional


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


def zfs_legacy_mount(dataset: str, mountpoint: str, call_args: Optional[list] = None):
    system_platform = platform.system().lower()

    mount_call = ["-t", "zfs"]
    if system_platform == "linux":
        """
        Temp mount on linux requires '-o zfsutil', see:
        https://github.com/zfsonlinux/zfs/issues/7452
        """
        mount_call.extend(["-o", "zfsutil"])

    if call_args:
        mount_call.extend(call_args)

    mount_call.extend([dataset, mountpoint])

    try:
        mount(call_args=mount_call)
    except RuntimeError as e:
        raise
