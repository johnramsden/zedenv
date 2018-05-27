"""List boot environments cli"""

import sys

from typing import Optional

import click
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility as zfs_utility

import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger


def get_clones(root_dataset: str,
               existing: Optional[str]) -> list:

    parent_dataset = zfs_utility.dataset_parent(root_dataset)

    clone_data = []
    list_dataset = None  # Dataset we are listing clones under

    if existing:
        existing_dataset = f"{parent_dataset}/{existing}"
        if zfs_utility.is_snapshot(existing_dataset):
            snap_suffix = existing_dataset.rsplit('@', 1)[-1]
            list_dataset = zfs_utility.snapshot_parent_dataset(existing_dataset)
        else:
            if zfs_utility.dataset_exists(existing_dataset):
                snap_suffix = zedenv.lib.be.snapshot(existing, parent_dataset)
                list_dataset = f"{parent_dataset}/{existing}"
            else:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"The dataset {existing_dataset} doesn't exist."
                }, exit_on_error=True)
    else:
        snap_suffix = zedenv.lib.be.snapshot(zfs_utility.dataset_child_name(root_dataset),
                                             parent_dataset)
        list_dataset = root_dataset

    clones = None
    try:
        clones = pyzfscmds.cmd.zfs_list(list_dataset, recursive=True, columns=["name"])
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to list datasets under {root_dataset}."
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
            clone_props = zedenv.lib.be.properties(
                c, [["canmount", "off"]])
            clone_data.append({
                "snapshot": f"{c}@{snap_suffix}",
                "properties": clone_props,
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


def zedenv_create(parent_dataset: str,
                  root_dataset: str,
                  boot_environment: str,
                  verbose: bool,
                  existing: Optional[str]):
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

    # Remove the final part of the data set after the last / and add new name
    boot_environment_dataset = f"{parent_dataset}/{boot_environment}"

    if zfs_utility.dataset_exists(boot_environment_dataset):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to create {boot_environment_dataset}, already exists."
        }, exit_on_error=True)

    # Getting snapshot for clone
    clone_sources = get_clones(root_dataset, existing)
    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Getting properties of {boot_environment_dataset} for clones {clone_sources}\n"
    }, verbose)

    for source in clone_sources:
        if source['datasetchild'] == '':
            be_clone = f"{boot_environment_dataset}"
        else:
            be_clone = f"{boot_environment_dataset}/{source['datasetchild']}"

        try:
            pyzfscmds.cmd.zfs_clone(source['snapshot'], be_clone, properties=source['properties'])
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
def cli(boot_environment: str, verbose: Optional[bool], existing: Optional[str]):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)

    parent_dataset = zedenv.lib.be.root()
    root_dataset = pyzfscmds.system.agnostic.mountpoint_dataset("/")

    zedenv_create(parent_dataset, root_dataset,
                  boot_environment, verbose, existing)
