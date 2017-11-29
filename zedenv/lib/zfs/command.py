"""ZFS library"""

import itertools
import subprocess


class ZFS:
    @staticmethod
    def _run(command, arguments):

        zfs_call = ["zfs", command] + arguments

        try:
            output = subprocess.check_output(zfs_call,
                                             universal_newlines=True,
                                             stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise e

        return output

    """
    ZFS commands
    """

    @classmethod
    def clone(cls, snapname: str, filesystem: str, properties: list = None, create_parent=False):

        if snapname is None:
            raise TypeError("Snapshot name cannot be of type 'None'")

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
        call_args.extend([snapname, filesystem])

        try:
            return cls._run("clone", call_args)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone {filesystem}\n{e.output}")

    @classmethod
    def get(cls, target: str, recursive=False, depth=None, scripting=True,
            parsable=False, columns: list = None, zfs_types: list = None,
            source: list = None, properties: list = None):
        """
        zfs get [-r|-d depth] [-Hp] [-o all | field[,field]...]
         [-t type[, type]...] [-s source[,source]...] all |
         property[,property]...	filesystem|volume|snapshot...
        """

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
            return cls._run("get", call_args)
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Failed to get zfs properties of {target}")

    @classmethod
    def list(cls, target: str, recursive=False, depth=None, scripting=True,
             parsable=False, columns: list = None, zfs_types: list = None,
             sort_properties_ascending: list = None, sort_properties_descending: list = None):
        """
        zfs list [-r|-d depth] [-Hp] [-o property[,property]...]
            [-t type[,type]...] [-s property]... [-S property]...
            filesystem|volume|snapshot
        """

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

        if sort_properties_ascending is not None:
            call_args.extend(
                [p for prop in sort_properties_ascending for p in ("-s", prop)])

        if sort_properties_descending is not None:
            call_args.extend(
                [p for prop in sort_properties_descending for p in ("-S", prop)])

        call_args.append(target)

        try:
            return cls._run("list", call_args)
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Failed to get zfs list of {target}")

    @classmethod
    def snapshot(cls, filesystem: str, snapname: str, recursive=False, properties=None):

        if snapname is None:
            raise TypeError("Snapshot name cannot be of type 'None'")

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
            cls._run("snapshot", call_args)
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Failed to snapshot {filesystem}")

