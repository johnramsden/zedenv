"""List boot environments cli"""

import sys

import click
import pyzfsutils.cmd
import pyzfsutils.system.agnostic
import pyzfsutils.utility as zfs_utility

import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger


def get_clones(dataset_source, existing) -> list:
    parent_dataset = zfs_utility.dataset_parent(dataset_source)

    clone_data = list()
    if existing:
        if zfs_utility.is_snapshot(existing):
            snap_suffix = existing.rsplit('@', 1)[-1]
            list_dataset = zfs_utility.snapshot_parent_dataset(existing)
        else:
            snap_suffix = zedenv.lib.be.snapshot(existing,
                                                 zfs_utility.dataset_parent(dataset_source))
            list_dataset = existing
    else:
        snap_suffix = zedenv.lib.be.snapshot(zfs_utility.dataset_child_name(dataset_source),
                                             parent_dataset)
        list_dataset = dataset_source

    clones = None
    try:
        clones = pyzfsutils.cmd.zfs_list(list_dataset, recursive=True, columns=["name"])
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to list datasets under {dataset_source}."
        }, exit_on_error=True)

    for c in [line for line in clones.splitlines()]:
        ZELogger.log({
            "level": "INFO",
            "message": f"Getting clone of {c}@{snap_suffix}."
        })

        if zfs_utility.dataset_exists(f"{c}@{snap_suffix}", zfs_type="snapshot"):
            if c == list_dataset:
                child = ""
            else:
                child = zfs_utility.dataset_child_name(c)
            clone_data.append({
                "snapshot": f"{c}@{snap_suffix}",
                "properties": zedenv.lib.be.properties(c, ["canmount=off"]),
                "datasetchild": child
            })
        else:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to find snapshot {c}@{snap_suffix}."
            }, exit_on_error=True)

    return clone_data


def show_source_properties(property_list, verbose):
    ZELogger.verbose_log({"level": "INFO", "message": "PROPERTIES"}, verbose)
    for p in property_list:
        ZELogger.verbose_log({"level": "INFO", "message": p}, verbose)
    ZELogger.verbose_log({"level": "INFO", "message": ""}, verbose)


def zedenv_create(parent_dataset, root_dataset, boot_environment, verbose, existing):
    """
    :Parameters:
      parent_dataset : str
        Dataset boot environment root, commonly 'zpool/ROOT'.
      root_dataset : str
        Current boot dataset.
      boot_environment : str
        Name of new boot environment, e.g. default-02
      verbose : bool
        Print information verbosely.
      existing : bool
        Create boot environment from certain dataset.
    :return:
    """

    ZELogger.verbose_log({
        "level": "INFO", "message": "Creating Boot Environment:\n"
    }, verbose)

    # Getting snapshot for clone
    clone_sources = get_clones(root_dataset, existing)

    # Remove the final part of the data set after the last / and add new name
    boot_environment_dataset = f"{parent_dataset}/{boot_environment}"

    ZELogger.verbose_log({
        "level": "INFO",
        "message": (f"Getting properties of {boot_environment_dataset}.\n"
                    f"for clones {clone_sources}\n")
    }, verbose)

    if zfs_utility.dataset_exists(boot_environment_dataset):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": (f"Failed to create {boot_environment_dataset}",
                        f" already exists.")
        }, exit_on_error=True)

    for source in clone_sources:
        if source['datasetchild'] == '':
            be_clone = f"{boot_environment_dataset}"
        else:
            be_clone = f"{boot_environment_dataset}/{source['datasetchild']}"

        try:
            pyzfsutils.cmd.zfs_clone(source['snapshot'], be_clone, properties=source['properties'])
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": (f"Failed to create {boot_environment_dataset}",
                            f" from {clone_sources['snapshot']}")
            }, exit_on_error=True)


@click.command(name="create",
               help="Create a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--existing', '-e',
              help="Use existing boot environment as source.")
@click.argument('boot_environment')
def cli(boot_environment, verbose, existing):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        sys.exit(err)

    parent_dataset = zedenv.lib.be.root()
    root_dataset = pyzfsutils.system.agnostic.mountpoint_dataset("/")

    zedenv_create(parent_dataset, root_dataset,
                  boot_environment, verbose, existing)
