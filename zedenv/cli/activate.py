"""List boot environments cli"""

import sys

import click

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


def mount_and_modify_dataset(dataset: str,
                             verbose: bool = False,
                             noop: bool = False,
                             pre_mount_properties: List[str] = None,
                             post_mount_properties: List[str] = None,
                             plugin=None):
    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Mount dataset for customization\n"
    }, verbose)

    if not noop:
        if pre_mount_properties:
            for pre_prop in pre_mount_properties:
                try:
                    pyzfscmds.cmd.zfs_set(dataset, pre_prop)
                except RuntimeError as e:
                    ZELogger.log({
                        "level": "EXCEPTION",
                        "message": f"Failed to set {pre_prop} on {dataset}\n{e}\n"
                    }, exit_on_error=True)

    # Allow even with noop, just mounts and runs plugin
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
                "level": "EXCEPTION", "message": f"Failed to mount mountpoint={tmpdir}\n{e}\n"
            }, exit_on_error=True)

        ZELogger.verbose_log(
            {"level": "INFO", "message": f"Mounted {dataset} to {tmpdir}\n"}, verbose)

        # Do stuff while mounted
        if plugin is not None:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Running plugin: '{plugin.bootloader}' - mid_activate\n"
            }, verbose)
            try:
                plugin.mid_activate(tmpdir)
            except RuntimeWarning as err:
                ZELogger.verbose_log({
                    "level": "WARNING",
                    "message": f"During {plugin.bootloader} mid activate the following occurred:\n"
                               f"\n{err}\nContinuing activation.\n"
                }, verbose)
            except RuntimeError as err:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"During {plugin.bootloader} mid activate the following occurred:\n"
                               f"\n{err}\nStopping activation.\n"
                }, exit_on_error=True)

        try:
            pyzfscmds.cmd.zfs_unmount(dataset)
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to unmount {dataset} from {tmpdir}\n{e}\n"
            }, exit_on_error=True)
        ZELogger.verbose_log(
            {"level": "INFO", "message": f"Unmounted {dataset} from {tmpdir}\n"}, verbose)

    if not noop:
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
                              noop: Optional[bool],
                              bootloader_plugin):

    if dataset_mountpoint != "/":
        if dataset_mountpoint:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Unmounting {dataset_mountpoint}.\n"
            }, verbose)

            if not noop:
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
                                 noop=noop,
                                 plugin=bootloader_plugin)

    if not noop:
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
    """
    Dont run if noop
    """
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

    canmount_setting = "canmount=noauto"
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
                    noconfirm: Optional[bool],
                    noop: Optional[bool]):
    """
    If a plugin is found that can be run on the system,
    run the activate command from the plugin.
    """

    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Activating Boot Environment: {boot_environment}\n"
    }, verbose)

    be_requested = f"{boot_environment_root}/{boot_environment}"

    zpool = zedenv.lib.be.dataset_pool(be_requested)
    current_be = None
    try:
        current_be = pyzfscmds.utility.dataset_child_name(
            zedenv.lib.be.bootfs_for_pool(zpool))
    except RuntimeError:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to get active boot environment'\n"
        }, exit_on_error=True)

    bootloader_plugin = None
    if bootloader:
        bootloader_plugin = zedenv.lib.configure.get_bootloader(
            boot_environment, current_be, bootloader, verbose, noconfirm, noop,
            boot_environment_root
        )
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Using plugin {bootloader}\n"
        }, verbose)

    if bootloader_plugin:
        try:
            bootloader_plugin.pre_activate()
        except RuntimeWarning as err:
            ZELogger.verbose_log({
                "level": "WARNING",
                "message": f"During {plugin.bootloader} pre activate the following occurred:\n"
                           f"\n{err}\nContinuing activation.\n"
            }, verbose)
        except RuntimeError as err:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"During {plugin.bootloader} pre activate the following occurred:\n"
                           f"\n{err}\nStopping activation.\n"
            }, exit_on_error=True)
        except AttributeError:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Tried to run {plugin.bootloader} 'pre activate', not implemented.\n"
            }, verbose)

    if not pyzfscmds.utility.dataset_exists(be_requested):
        ds_is_clone = None
        try:
            ds_is_clone = pyzfscmds.utility.is_clone(be_requested)
        except RuntimeError:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Boot environment {boot_environment} doesn't exist'\n"
            }, exit_on_error=True)

        if not ds_is_clone:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Boot environment {boot_environment} doesn't exist'\n"
            }, exit_on_error=True)

    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Boot environment {boot_environment} exists'\n"
    }, verbose)

    if current_be == be_requested:
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Boot Environment {boot_environment} is already active.\n"
        }, verbose)
    else:
        # Set bootfs on dataset
        dataset_mountpoint = pyzfscmds.system.agnostic.dataset_mountpoint(be_requested)
        activate_boot_environment(
            be_requested, dataset_mountpoint, verbose, noop, bootloader_plugin)

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
    if not noop:
        disable_children_automount(be_child_datasets_list,
                                   be_requested,
                                   boot_environment_root,
                                   verbose)

        apply_settings_to_child_datasets(be_child_datasets_list, be_requested, verbose)

    if bootloader_plugin:
        try:
            bootloader_plugin.post_activate()
        except RuntimeWarning as err:
            ZELogger.verbose_log({
                "level": "WARNING",
                "message": f"During {plugin.bootloader} post activate the following occurred:\n"
                           f"\n{err}\nContinuing activation.\n"
            }, verbose)
        except RuntimeError as err:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"During {plugin.bootloader} post activate the following occurred:\n"
                           f"\n{err}\nStopping activation.\n"
            }, exit_on_error=True)
        except AttributeError:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Tried to run {plugin.bootloader} 'post activate', not implemented.\n"
            }, verbose)


@click.command(name="activate",
               help="Activate a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--bootloader', '-b',
              help="Use bootloader type.")
@click.option('--noconfirm', '-y',
              is_flag=True,
              help="Assume yes in situations where confirmation is needed.")
@click.option('--noop', '-n',
              is_flag=True,
              help="Print what would be done, but don't apply.")
@click.argument('boot_environment')
def cli(boot_environment: str,
        verbose: Optional[bool],
        bootloader: Optional[str],
        noconfirm: Optional[bool],
        noop: Optional[bool]):

    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)

    boot_environment_root = zedenv.lib.be.root()

    bootloader_set = zedenv.lib.be.get_property(
        f"{boot_environment_root}/{boot_environment}", "org.zedenv:bootloader")
    if not bootloader and bootloader_set:
        bootloader = bootloader_set if bootloader_set != '-' else None

    if noconfirm and not bootloader:
        sys.exit("The '--noconfirm/-y' flag requires the bootloader option '--bootloader/-b'.")

    zedenv_activate(boot_environment,
                    boot_environment_root,
                    verbose,
                    bootloader,
                    noconfirm,
                    noop)
