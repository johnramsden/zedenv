"""List boot environments cli"""

import datetime

import click

from zedenv.lib.zfs.command import ZFS
import zedenv.lib.zfs.utility as zfs_utility
import zedenv.lib.zfs.linux as zfs_linux

import zedenv.lib.boot_environment as be

from zedenv.lib.logger import ZELogger


def get_clone_sources(root_dataset, existing) -> dict:

    clone_sources = dict()

    if existing:
        if zfs_utility.is_snapshot(existing):
            clone_sources['snapshot'] = existing
            clone_sources['properties'] = zfs_utility.snapshot_parent_dataset(existing)
        else:
            clone_sources['snapshot'] = get_source_snapshot(existing)
            clone_sources['properties'] = be.get_full_dataset(existing)
    else:
        clone_sources['snapshot'] = get_source_snapshot(
                                        zfs_utility.dataset_child_name(root_dataset))
        clone_sources['properties'] = root_dataset

    return clone_sources


def get_source_snapshot(boot_environment_name, snap_prefix="zedenv"):

    if "/" in boot_environment_name:
        ZELogger.log({
            "level":   "EXCEPTION",
            "message": f"Failed to get snapshot.\n"
                       f"Existing boot environment name {boot_environment_name} should not contain '/'"
        }, exit_on_error=True)

    boot_environment_root = be.get_root()

    dataset_name = f"{boot_environment_root}/{boot_environment_name}"

    snap_suffix = "{prefix}-{suffix}".format(
        prefix=snap_prefix,
        suffix=datetime.datetime.now().isoformat())

    try:
        ZFS.snapshot(dataset_name, snap_suffix)
    except RuntimeError:
        ZELogger.log({
            "level":   "EXCEPTION",
            "message": f"Failed to create snapshot: '{dataset_name}@{snap_suffix}'"
        }, exit_on_error=True)

    return f"{dataset_name}@{snap_suffix}"


def boot_env_properties(dataset):

    try:
        properties = ZFS.get(dataset,
                             columns=["property", "value"],
                             source=["local", "received"],
                             properties=["all"])
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION", "message": f"Failed to get properties of '{dataset}'"
        }, exit_on_error=True)

    """
    Take each line of output containing properties and convert
    it to a list of property=value strings
    """
    property_list = ["=".join(line.split()) for line in properties.splitlines()]
    if "canmount=off" not in property_list:
        property_list.append("canmount=off")

    return property_list


def show_source_properties(property_list, verbose):
    ZELogger.verbose_log({"level": "INFO", "message": "PROPERTIES"}, verbose)
    for p in property_list:
        ZELogger.verbose_log({"level": "INFO", "message": p}, verbose)
    ZELogger.verbose_log({"level": "INFO", "message": ""}, verbose)


@click.command(name="create",
               help="Create a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--existing', '-e',
              help="Use existing boot environment as source.")
@click.argument('boot_environment')
def cli(boot_environment, verbose, existing, test, setroot):

    parent_dataset = be.get_root()

    root_dataset = zfs_linux.mount_dataset("/")

    ZELogger.verbose_log({
        "level":   "INFO", "message": "Creating Boot Environment:\n"
    }, verbose)

    # Getting snapshot for clone
    clone_sources = get_clone_sources(root_dataset, existing)

    # Remove the final part of the data set after the last / and add new name
    boot_environment_dataset = f"{parent_dataset}/{boot_environment}"

    ZELogger.verbose_log({
        "level":   "INFO", "message": f"Getting properties of {clone_sources['properties']}.\n"
    }, verbose)

    property_list = boot_env_properties(clone_sources['properties'])
    show_source_properties(property_list, verbose)

    ZELogger.verbose_log({
        "level": "INFO", "message": f"Using {clone_sources['snapshot']} as source\n"
                                    f"Creating Boot Environment: {boot_environment_dataset}\n"
    }, verbose)

    try:
        ZFS.clone(clone_sources['snapshot'],
                  boot_environment_dataset,
                  properties=property_list)
    except RuntimeError as e:
        ZELogger.log({
           "level":   "EXCEPTION",
           "message": f"Failed to create {boot_environment_dataset} from {clone_sources['snapshot']}"
        }, exit_on_error=True)
