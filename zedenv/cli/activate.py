"""List boot environments cli"""

import sys

import click
import platform
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility
import tempfile
from typing import Optional, List

import zedenv.lib.be
import zedenv.lib.check
import zedenv.lib.configure
import zedenv.lib.system
from zedenv.lib.logger import ZELogger


def get_bootloader(boot_environment: str,
                   bootloader: str,
                   verbose: bool,
                   legacy: bool):
    bootloader_plugin = None
    if bootloader:
        plugins = zedenv.lib.configure.get_plugins()
        if bootloader in plugins:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": ("Configuring boot environment "
                            f"bootloader with {bootloader}\n")
            }, verbose)
            if platform.system().lower() in plugins[bootloader].systems_allowed:
                bootloader_plugin = plugins[bootloader](
                    boot_environment, bootloader, verbose, legacy)
            else:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": (f"The plugin {bootloader} is "
                                f"not valid for {platform.system().lower()}\n")
                }, exit_on_error=True)
        else:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"bootloader type {bootloader} does not exist\n"
                           "Check available plugins with 'zedenv --plugins'\n"
            }, exit_on_error=True)

    return bootloader_plugin


def mount_and_modify_dataset(dataset: str,
                             verbose: bool = False,
                             pre_mount_properties: List[str] = None,
                             post_mount_properties: List[str] = None,
                             plugin=None):
    if pre_mount_properties:
        for pre_prop in pre_mount_properties:
            try:
                pyzfscmds.cmd.zfs_set(dataset, pre_prop)
            except RuntimeError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Failed to set {pre_prop} on {dataset}\n{e}\n"
                }, exit_on_error=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            pyzfscmds.cmd.zfs_set(dataset, f"mountpoint={tmpdir}")
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION", "message": f"Failed to set mountpoint={tmpdir}\n{e}\n"
            }, exit_on_error=True)

        try:
            pyzfscmds.cmd.zfs_mount(dataset)
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION", "message": f"Failed to mount mountpoint={dataset}\n{e}\n"
            }, exit_on_error=True)

        ZELogger.verbose_log(
            {"level": "INFO", "message": f"Mounted {dataset} to {tmpdir}\n"}, verbose)

        # Do stuff while mounted
        if plugin is not None:
            ZELogger.verbose_log({
                "level": "INFO", "message": f"Ran plugin:\n{plugin.bootloader_modify()}\n"
            }, verbose)

            # TODO

        try:
            pyzfscmds.cmd.zfs_unmount(dataset)
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to unmount {dataset} from {tmpdir}\n{e}\n"
            }, exit_on_error=True)
        ZELogger.verbose_log(
            {"level": "INFO", "message": f"Unmounted {dataset} from {tmpdir}\n"}, verbose)

    if post_mount_properties:
        for post_prop in post_mount_properties:
            try:
                pyzfscmds.cmd.zfs_set(dataset, post_prop)
            except RuntimeError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Failed to set {post_prop} on {dataset}\n{e}\n"
                }, exit_on_error=True)


def activate_boot_environment(be_requested: str,
                              dataset_mountpoint: Optional[str],
                              verbose: Optional[bool],
                              bootloader_plugin):
    if dataset_mountpoint and dataset_mountpoint != "/":
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Unmounting {dataset_mountpoint}.\n"
        }, verbose)

        try:
            zedenv.lib.system.umount(dataset_mountpoint)
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed unmounting dataset {be_requested}\n{e}\n"
            }, exit_on_error=True)

        mount_and_modify_dataset(be_requested,
                                 pre_mount_properties=["canmount=noauto"],
                                 post_mount_properties=["mountpoint=/"],
                                 verbose=verbose,
                                 plugin=bootloader_plugin)

    try:
        pyzfscmds.cmd.zpool_set(zedenv.lib.be.dataset_pool(be_requested),
                                f"bootfs={be_requested}")
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION", "message": f"Failed to set bootfs to {be_requested}\n{e}\n"
        }, exit_on_error=True)


def disable_children_automount(be_child_datasets: List[str],
                               be_requested: str,
                               boot_environment_root: str,
                               verbose: Optional[bool]):
    for ds in be_child_datasets:
        if not (be_requested in ds) and not (boot_environment_root == ds):
            try:
                pyzfscmds.cmd.zfs_set(ds, "canmount=noauto")
            except RuntimeError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Failed to set canmount=noauto on {ds}\n{e}\n"
                }, exit_on_error=True)
            ZELogger.verbose_log({"level": "INFO",
                                  "message": f"Disabled automount for {ds}\n"}, verbose)


def apply_settings_to_child_datasets(be_child_datasets_list, be_requested, verbose):

    # TODO: Should this be noauto?
    canmount_setting = "canmount=on"
    for ds in be_child_datasets_list:
        if be_requested == ds:
            try:
                pyzfscmds.cmd.zfs_set(ds, canmount_setting)
            except RuntimeError:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Failed to set {canmount_setting} for {ds}\n{e}\n"
                }, exit_on_error=True)

            if pyzfscmds.utility.is_clone(ds):
                try:
                    pyzfscmds.cmd.zfs_promote(ds)
                except RuntimeError:
                    ZELogger.log({
                        "level": "EXCEPTION",
                        "message": f"Failed to promote BE {ds}\n{e}\n"
                    }, exit_on_error=True)
                ZELogger.verbose_log(
                    {"level": "INFO", "message": f"Promoted {ds}.\n"}, verbose)


def zedenv_activate(boot_environment: str,
                    boot_environment_root: str,
                    verbose: Optional[bool],
                    bootloader: Optional[str],
                    legacy: Optional[bool]):
    """
    If a plugin is found that can be run on the system,
    run the activate command from the plugin.
    """

    bootloader_plugin = get_bootloader(
        boot_environment, bootloader, verbose, legacy) if bootloader else None

    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Activating Boot Environment: {boot_environment}\n"
    }, verbose)

    be_requested = f"{boot_environment_root}/{boot_environment}"

    if not pyzfscmds.utility.dataset_exists(
            be_requested) and not pyzfscmds.utility.is_clone(be_requested):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Boot environment {boot_environment} doesn't exist'\n"
        }, exit_on_error=True)
    else:
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Boot environment {boot_environment} exists'\n"
        }, verbose)

    if zedenv.lib.be.is_active_boot_environment(be_requested,
                                                zedenv.lib.be.dataset_pool(be_requested)):
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Boot Environment {boot_environment} is already active.\n"
        }, verbose)
    else:
        dataset_mountpoint = pyzfscmds.system.agnostic.dataset_mountpoint(be_requested)
        activate_boot_environment(be_requested, dataset_mountpoint, verbose, bootloader_plugin)

    be_child_datasets = None
    try:
        be_child_datasets = pyzfscmds.cmd.zfs_list(boot_environment_root,
                                                   recursive=True,
                                                   columns=["name"],
                                                   zfs_types=["filesystem"])
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to list datasets under {boot_environment_root}\n{e}\n"
        }, exit_on_error=True)

    be_child_datasets_list = [line for line in be_child_datasets.splitlines()]
    disable_children_automount(be_child_datasets_list,
                               be_requested,
                               boot_environment_root,
                               verbose)

    apply_settings_to_child_datasets(be_child_datasets_list, be_requested, verbose)


@click.command(name="activate",
               help="Activate a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--bootloader', '-b',
              help="Use bootloader type.")
@click.option('--legacy', '-l',
              is_flag=True,
              help="Legacy mountpoint type.")
@click.argument('boot_environment')
def cli(boot_environment, verbose, bootloader, legacy):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        sys.exit(err)

    zedenv_activate(boot_environment, zedenv.lib.be.root(), verbose, bootloader, legacy)
