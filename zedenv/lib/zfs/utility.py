"""ZFS library"""

from zedenv.lib.zfs.command import ZFS

"""
ZFS helper functions
"""


def is_snapshot(snapname) -> bool:
    if "@" in snapname:
        return dataset_exists(snapname)

    return False


"""
Check if clone, raise if not valid dataset
"""


def is_clone(dataset) -> bool:
    try:
        origin = ZFS.get(dataset,
                         properties=["origin"],
                         columns=["value"])
        print(origin)
    except RuntimeError:
        raise

    if origin.split()[0] == "-":
        return False

    return True


def dataset_parent(dataset):
    # TODO: Should I check ds valid?
    return dataset.rsplit('/', 1)[0]


def dataset_child_name(dataset):
    return dataset.rsplit('/', 1)[-1]


def snapshot_parent_dataset(dataset):
    return dataset.rsplit('@', 1)[-2]


def dataset_exists(target) -> bool:

    try:
        ZFS.list(target)
    except RuntimeError:
        return False

    return True
