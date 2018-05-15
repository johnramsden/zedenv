import subprocess
from typing import List


def mount(call_args: List[str] = None,
          mount_command: str = "mount"):

    mount_call = [mount_command]
    if call_args:
        mount_call.extend(call_args)

    try:
        mount_output = subprocess.check_output(
            mount_call, universal_newlines=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        raise RuntimeError(f"Failed to get mount data")

    mount_list = mount_output.splitlines()

    return mount_list


def umount(target: str, call_args: List[str] = None):
    umount_args = []
    if call_args:
        umount_args.extend(call_args)

    umount_args.append(target)

    try:
        umount_output = mount(umount_args, mount_command="umount")
    except RuntimeError:
        raise RuntimeError(f"Failed to unmount {target}")

    return umount_output
