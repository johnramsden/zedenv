"""ZFS library"""

import subprocess
import itertools


class ZFS:
    def __init__(self):
        pass

    def clone(self, snapshot, filesystem, properties=None, create_parent=False):

        if create_parent:
            call_args = ["-p"]
        else:
            call_args = []

        """Combine all arguments with properties"""
        if properties is not None:
            prop_list = [["-o", prop] for prop in properties]
            call_args.extend(list(itertools.chain.from_iterable(prop_list)))

        call_args.extend([snapshot, filesystem])

        clone_show = ["zfs", "clone"] + call_args

        """Make sure is snapshot"""
        try:
            print(clone_show)
            # subprocess.check_call(
            #     ["zfs", "clone"].extend(call_args), stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise RuntimeError("Failed to create snapshot")
