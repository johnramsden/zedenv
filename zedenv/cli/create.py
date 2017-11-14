"""List boot environments cli"""

import datetime

import click

import zedenv.lib.zfs.command as zfs_command
import zedenv.lib.zfs.utility as zfs_utility
import zedenv.lib.zfs.linux as zfs_linux

from zedenv.lib.logger import ZELogger


def get_boot_environment_root():
    return zfs_utility.dataset_parent(zfs_linux.mount_dataset("/"))


def full_dataset_from_name(name):
    return f"{get_boot_environment_root()}/{name}"


def get_source_snapshot(boot_environment_name, snap_prefix="zedenv"):

    boot_environment_root = get_boot_environment_root()

    dataset_name = f"{boot_environment_root}/{boot_environment_name}"

    snap_suffix = "{prefix}-{suffix}".format(
        prefix=snap_prefix,
        suffix=datetime.datetime.now().isoformat())

    try:
        zfs_command.snapshot(dataset_name, snap_suffix)
    except RuntimeError:
        ZELogger.log({
            "level":   "EXCEPTION",
            "message": f"Failed to create snapshot: '{dataset_name}@{snap_suffix}'"
        }, exit_on_error=True)

    return f"{dataset_name}@{snap_suffix}"


def boot_env_properties(dataset):

    try:
        properties = zfs_command.get(dataset,
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
@click.option('--test', '-t',
              is_flag=True,
              help="Create test BE from date.")
@click.option('--existing', '-e',
              help="Use existing boot environment as source.")
@click.argument('boot_environment')
def cli(boot_environment, verbose, existing, test):

    if test:
        boot_environment = f"zedenv-{datetime.datetime.now().isoformat()}"

    parent_dataset = get_boot_environment_root()
    root_dataset = zfs_linux.mount_dataset("/")

    ZELogger.verbose_log({
        "level":   "INFO", "message": "Creating Boot Environment:\n"
    }, verbose)

    # Getting snapshot for clone
    if existing:
        if zfs_utility.is_snapshot(existing):
            source_snapshot = existing
            property_source = zfs_utility.snapshot_parent_dataset(existing)
        else:
            source_snapshot = get_source_snapshot(existing)
            property_source = full_dataset_from_name(existing)
    else:
        source_snapshot = get_source_snapshot(zfs_utility.dataset_child_name(root_dataset))
        property_source = root_dataset

    # Remove the final part of the data set after the last / and add new name
    boot_environment_dataset = f"{parent_dataset}/{boot_environment}"

    ZELogger.verbose_log({
        "level":   "INFO", "message": f"Getting properties of {property_source}.\n"
    }, verbose)

    property_list = boot_env_properties(property_source)
    show_source_properties(property_list, verbose)

    ZELogger.verbose_log({
        "level": "INFO", "message": f"Using {source_snapshot} as source\n"
                                    f"Creating Boot Environment: {boot_environment_dataset}\n"
    }, verbose)

    try:
        zfs_command.clone(source_snapshot,
                          boot_environment_dataset,
                          properties=property_list)
    except RuntimeError as e:
        ZELogger.log({
           "level":   "EXCEPTION",
           "message": f"Failed to create {boot_environment_dataset} from {source_snapshot}"
        }, exit_on_error=True)
