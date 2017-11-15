"""List boot environments cli"""

import datetime

import click
import zedenv.lib.zfs.commands
import zedenv.lib.zfs.linux
from zedenv.lib.logger import ZELogger

@click.command(name="create",
               help="Create a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--existing', '-e',
              is_flag=True,
              help="Use existing boot environment as source.")
@click.argument('boot_environment')
def cli(boot_environment, verbose, existing):

    ZELogger.verbose_log({
        "level":   "INFO",
        "message": "Creating Boot Environment:\n"
    }, verbose)

    zfs = zedenv.lib.zfs.commands.ZFS()
    root_dataset = zedenv.lib.zfs.linux.mount_dataset("/")

    ZELogger.verbose_log({
        "level":   "INFO",
        "message": f"Getting properties of {root_dataset}.\n"
    }, verbose)

    try:
        properties = zfs.get(root_dataset,
                             columns=["property", "value"],
                             source=["local", "received"],
                             properties=["all"])
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to get properties of '{root_dataset}'"
        }, exit_on_error=True)

    """
    Take each line of output containing properties and convert
    it to a list of property=value strings
    """
    property_list = ["=".join(line.split()) for line in properties.splitlines()]
    if "canmount=off" not in property_list:
        property_list.append("canmount=off")

    # VERBOSE: Show all properties
    ZELogger.verbose_log({"level": "INFO","message": "PROPERTIES"}, verbose)
    for p in property_list:
        ZELogger.verbose_log({"level": "INFO", "message": p}, verbose)
    ZELogger.verbose_log({"level": "INFO", "message": ""}, verbose)

    if existing:
        source_snap = existing
    else:
        snap_suffix = "zedenv-{}".format(datetime.datetime.now().isoformat())
        try:
            zfs.snapshot(root_dataset, snap_suffix)
        except RuntimeError:
            ZELogger.log({
                "level":   "EXCEPTION",
                "message": f"Failed to create snapshot: '{root_dataset}@{snap_suffix}'"
            }, exit_on_error=True)

        source_snap = f"{root_dataset}@{snap_suffix}"

    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Using {source_snap} as source"
    }, verbose)

    # Remove the final part of the data set after the last / and add new name
    boot_environment_dataset = f"{root_dataset.rsplit('/', 1)[0]}/{boot_environment}"

    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Creating Boot Environment: {boot_environment_dataset}"
    }, verbose)

    try:
        zfs.clone(source_snap,
                  boot_environment_dataset,
                  properties=property_list)
    except RuntimeError:
        ZELogger.log({
               "level":   "EXCEPTION",
               "message": f"Failed to create {boot_environment} from {source_snap}"
        }, exit_on_error=True)
