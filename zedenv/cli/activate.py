"""List boot environments cli"""

import sys
import platform
from typing import Callable

import click

import zedenv.lib.configure
from zedenv.lib.logger import ZELogger
import zedenv.lib.check


def get_bootloader(boot_environment: str,
                   verbose: bool,
                   bootloader: str,
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
                        boot_environment, verbose, bootloader, legacy)
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


def zedenv_activate(boot_environment: str,
                    verbose: bool,
                    bootloader: str,
                    legacy: bool):
    """
    :Parameters:
      boot_environment : str
        Name of boot environment to activate
      verbose : bool
        Print information verbosely.
    :return:
    """

    bootloader_plugin = get_bootloader(
        boot_environment, verbose, bootloader, legacy) if bootloader else None

    ZELogger.verbose_log({
        "level": "INFO",
        "message": f"Activating Boot Environment: {boot_environment}\n"
    }, verbose)

    if bootloader_plugin is not None:
        bootloader_plugin.activate()

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

    zedenv_activate(boot_environment, verbose, bootloader, legacy)
