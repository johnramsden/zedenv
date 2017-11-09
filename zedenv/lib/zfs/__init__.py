"""ZFS library"""

import subprocess
import itertools


class ZFS:
    def __init__(self, pool=None):
        self.pool = pool

    def __zfs_run(self, command, arguments):

        clone_call = ["zfs", command] + arguments

        try:
            subprocess.check_call(clone_call, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Failed to run 'zfs {command}'")

    def snapshot(self, filesystem, snapname, recursive=False, properties=None):

        if recursive:
            call_args = ["-r"]
        else:
            call_args = []

        """
        Combine all arguments with properties
        """
        if properties is not None:
            prop_list = [["-o", prop] for prop in properties]
            call_args.extend(
                list(itertools.chain.from_iterable(prop_list)))

        """
        Specify source filesystem and  snapshot name
        """
        call_args.append(f"{filesystem}@{snapname}")
        print(call_args)

        self.__zfs_run("snapshot", call_args)

    def clone(self, snapshot, filesystem, properties=None, create_parent=False):

        if create_parent:
            call_args = ["-p"]
        else:
            call_args = []

        """
        Combine all arguments with properties
        """
        if properties is not None:
            prop_list = [["-o", prop] for prop in properties]
            call_args.extend(list(itertools.chain.from_iterable(prop_list)))

        """
        Specify source snapshot and filesystem
        """
        call_args.extend([snapshot, filesystem])

        self.__zfs_run("clone", call_args)
