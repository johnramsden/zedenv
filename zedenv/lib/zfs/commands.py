"""ZFS library"""

import itertools
import subprocess



class ZFS:
    def __init__(self, pool=None):
        self.pool = pool

    def __zfs_run(self, command, arguments):

        zfs_call = ["zfs", command] + arguments

        try:
            return subprocess.check_output(zfs_call,
                                           universal_newlines=True,
                                           stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise

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
            call_args.extend(list(itertools.chain.from_iterable(prop_list)))

        """
        Specify source filesystem and  snapshot name
        """
        call_args.append(f"{filesystem}@{snapname}")

        try:
            self.__zfs_run("snapshot", call_args)
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Failed to snapshot {filesystem}")

    """
    zfs get [-r|-d depth] [-Hp] [-o all | field[,field]...]
	 [-t type[, type]...] [-s source[,source]...] all |
	 property[,property]...	filesystem|volume|snapshot...
    """
    # zfs get -o property,value -s local,received -H all
    def get(self, target, recursive=False, depth=None, scripting=True,
            parsable=False, columns: list=None, zfs_types: list=None,
            source: list=None, properties: list=None):

        call_args = []

        if recursive:
            call_args.append("-r")

        if depth is not None:
            call_args.extend(["-d", depth])

        if scripting:
            call_args.append("-H")

        if parsable:
            call_args.append("-p")

        if columns is not None:
            if "all" in columns:
                call_args.extend(["-o", "all"])
            else:
                call_args.extend(["-o", ",".join(columns)])

        if zfs_types is not None:
            call_args.extend(["-t", ",".join(zfs_types)])

        if source is not None:
            call_args.extend(["-s", ",".join(source)])

        if properties is None:
            call_args.append("all")
        else:
            call_args.append(",".join(properties))

        call_args.append(target)

        try:
            return self.__zfs_run("get", call_args)
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Failed to get zfs properties of {target}")

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

        try:
            self.__zfs_run("clone", call_args)
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Failed to clone {filesystem}")

