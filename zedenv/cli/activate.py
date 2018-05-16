"""List boot environments cli"""

import os
import sys
import platform
import tempfile

from typing import Optional, Callable

import click

import pyzfsutils.cmd
import pyzfsutils.system.agnostic
import pyzfsutils.utility

import zedenv.lib.be
import zedenv.lib.configure
import zedenv.lib.check
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
                             plugin=None):
    try:
        pyzfsutils.cmd.zfs_set(dataset, "canmount=noauto")
    except RuntimeError as e:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Failed to set canmount=noauto on {e}\n"
        }, exit_on_error=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            pyzfsutils.cmd.zfs_set(dataset, f"mountpoint={tmpdir}")
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to set mountpoint={tmpdir}\n{e}\n"
            }, exit_on_error=True)

        try:
            pyzfsutils.cmd.zfs_mount(dataset)
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to set mountpoint={tmpdir}\n{e}\n"
            }, exit_on_error=True)

        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Mounted {dataset} to {tmpdir}\n"
        }, verbose)

        # Do stuff while mounted
        if plugin is not None:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Ran plugin:\n{plugin.bootloader_modify()}\n"
            }, verbose)

            # TODO

        try:
            pyzfsutils.cmd.zfs_unmount(dataset)
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to unmount {dataset} from {tmpdir}\n{e}\n"
            }, exit_on_error=True)
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Unmounted {dataset} from {tmpdir}\n"
        }, verbose)


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

    be_requested = "/".join([boot_environment_root, boot_environment])

    if not pyzfsutils.utility.dataset_exists(
            be_requested) and not pyzfsutils.utility.is_clone(be_requested):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Boot environment {boot_environment} doesn't exist'\n"
        }, exit_on_error=True)
    else:
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Boot environment {boot_environment} exists'\n"
        }, verbose)

    if zedenv.lib.be.is_current_boot_environment(boot_environment):
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Boot Environment {boot_environment} is already active.\n"
        }, verbose)
    else:
        dataset_mountpoint = pyzfsutils.system.agnostic.dataset_mountpoint(be_requested)
        if dataset_mountpoint:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Boot Environment is mounted at {dataset_mountpoint}.\n"
            }, verbose)
            if dataset_mountpoint == "/":
                ZELogger.verbose_log({
                    "level": "INFO",
                    "message": f"Since dataset is current root, do not unmount.\n"
                }, verbose)
            else:
                ZELogger.verbose_log({
                    "level": "INFO",
                    "message": f"Unmounting {dataset_mountpoint}.\n"
                }, verbose)

                try:
                    zedenv.lib.system.umount(dataset_mountpoint)
                except RuntimeError as e:
                    ZELogger.log({
                        "level": "EXCEPTION",
                        "message": f"Failed unmounting dataset {boot_environment}\n{e}\n"
                    }, exit_on_error=True)
        else:
            ZELogger.verbose_log({
                "level": "INFO", "message": f"Boot Environment isn't mounted.\n"}, verbose)

        mount_and_modify_dataset(be_requested,
                                 verbose=verbose,
                                 plugin=bootloader_plugin)


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
