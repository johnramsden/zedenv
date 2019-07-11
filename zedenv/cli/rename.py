"""List boot environments cli"""
import errno

import click
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility as zfs_utility

import zedenv.lib.be
import zedenv.lib.check
import zedenv.lib.configure
from zedenv.lib.logger import ZELogger
from typing import Optional


def zedenv_rename(be_root: str,
                  boot_environment: str,
                  new_boot_environment: str,
                  bootloader: Optional[str],
                  verbose: Optional[bool]):

    old_be_dataset = f"{be_root}/{boot_environment}"
    new_be_dataset = f"{be_root}/{new_boot_environment}"

    zpool = zedenv.lib.be.dataset_pool(old_be_dataset)
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
            boot_environment, current_be, bootloader, verbose, False, False,
            be_root
        )
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Using plugin {bootloader}\n"
        }, verbose)

    dataset_mountpoint = pyzfscmds.system.agnostic.dataset_mountpoint(old_be_dataset)

    if pyzfscmds.utility.dataset_exists(new_be_dataset):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Boot environment '{new_boot_environment}' already exists.\n"
        }, exit_on_error=True)

    if zedenv.lib.be.is_current_boot_environment(boot_environment):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Cannot rename current boot environment '{boot_environment}.\n"
        }, exit_on_error=True)

    if zedenv.lib.be.is_active_boot_environment(old_be_dataset,
                                                zedenv.lib.be.dataset_pool(old_be_dataset)):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Cannot rename active boot environment '{boot_environment}.\n"
        }, exit_on_error=True)

    if dataset_mountpoint:
        ZELogger.log({
            "level": "EXCEPTION",
            "message": f"Dataset is mounted to '{dataset_mountpoint}', unmount and try again\n"
        }, exit_on_error=True)

    try:
        pyzfscmds.cmd.zfs_rename(old_be_dataset, new_be_dataset)
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)

    # Rename the boot dataset if a separate ZFS boot pool is used
    if zedenv.lib.be.extra_bpool():
        boot_dataset = pyzfscmds.system.agnostic.mountpoint_dataset('/boot')
        be_boot = zedenv.lib.be.root('/boot')
        old_be_boot_dataset = f"{be_boot}/zedenv-{boot_environment}"
        new_be_boot_dataset = f"{be_boot}/zedenv-{new_boot_environment}"
        try:
            pyzfscmds.cmd.zfs_rename(old_be_boot_dataset, new_be_boot_dataset)
        except RuntimeError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": (f"Failed to rename the boot dataset '{old_be_boot_dataset}' to"
                            f" '{new_be_boot_dataset}'. The following error occured:\n\n{e}"
                            "\nStopping rename.\n")
            }, exit_on_error=True)

    if bootloader_plugin:
        try:
            bootloader_plugin.post_rename()
        except RuntimeWarning as err:
            ZELogger.verbose_log({
                "level": "WARNING",
                "message": f"During {bootloader_plugin.bootloader} post rename the following"
                           f" occurred:\n\n{err}\nContinuing rename.\n"
            }, verbose)
        except RuntimeError as err:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"During {bootloader_plugin.bootloader} post rename the following "
                           f"occurred:\n\n{err}\nStopping rename.\n"
            }, exit_on_error=True)
        except AttributeError:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Tried to run {bootloader_plugin.bootloader} 'post rename', "
                           f"not implemented.\n"
            }, verbose)


@click.command(name="rename",
               help="Rename a boot environment.")
@click.option('--bootloader', '-b',
              help="Use bootloader type.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.argument('boot_environment')
@click.argument('new_boot_environment')
def cli(boot_environment: str, new_boot_environment: str, bootloader: Optional[str],
        verbose: Optional[str]):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)

    try:
        with zedenv.lib.check.Pidfile():

            boot_environment_root = zedenv.lib.be.root()

            bootloader_set = zedenv.lib.be.get_property(
                boot_environment_root, "org.zedenv:bootloader")
            if not bootloader and bootloader_set:
                bootloader = bootloader_set if bootloader_set != '-' else None

            zedenv_rename(boot_environment_root, boot_environment,
                          new_boot_environment, bootloader, verbose)

    except IOError as e:
        if e[0] == errno.EPERM:
            ZELogger.log({
                "level": "EXCEPTION", "message":
                    "You need root permissions to rename"
            }, exit_on_error=True)
    except zedenv.lib.check.ProcessRunningException as pr:
        ZELogger.log({
            "level": "EXCEPTION", "message":
                f"Already running zedenv.\n {pr}"
        }, exit_on_error=True)
