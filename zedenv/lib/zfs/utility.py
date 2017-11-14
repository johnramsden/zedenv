"""ZFS library"""

import subprocess

"""
ZFS helper functions
"""


def is_snapshot(snapname):
    # TODO: Check exists
    if "@" in snapname:
        return True
    else:
        return False


def dataset_parent(dataset):
    # TODO: Should I check ds valid?
    return dataset.rsplit('/', 1)[0]


def dataset_child_name(dataset):
    return dataset.rsplit('/', 1)[-1]


def snapshot_parent_dataset(dataset):
    return dataset.rsplit('@', 1)[-2]


