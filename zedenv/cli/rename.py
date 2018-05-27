"""List boot environments cli"""

import click
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import pyzfscmds.utility as zfs_utility

import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger


@click.command(name="rename",
               help="Rename a boot environment.")
@click.argument('boot_environment')
@click.argument('new_boot_environment')
def cli(boot_environment: str, new_boot_environment: str):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)

    be_root = zedenv.lib.be.root()
    old_be_dataset = f"{be_root}/{boot_environment}"
    new_be_dataset = f"{be_root}/{new_boot_environment}"
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
