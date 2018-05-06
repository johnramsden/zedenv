"""List boot environments cli"""

import click

import zedenv.lib.configure
import zedenv.lib.boot_environment as be
from zedenv.lib.logger import ZELogger


def get_bootloader(boot_environment, verbose, bootloader, legacy):
    bootloader_plugin = None
    if bootloader:
        plugins = zedenv.lib.configure.get_plugins()
        if bootloader in plugins:
                ZELogger.verbose_log({
                    "level": "INFO",
                    "message": "Configuring boot environment "
                               f"bootloader with {bootloader}\n"
                }, verbose)
                bootloader_plugin = plugins[bootloader](
                    boot_environment, verbose, bootloader, legacy)
        else:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"bootloader type {bootloader} does not exist\n"
                           "Check available plugins with 'zedenv --plugins'\n"
            }, exit_on_error=True)

    return bootloader_plugin


def zedenv_activate(boot_environment, verbose, bootloader, legacy):
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

    # if be.root()


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
    zedenv_activate(boot_environment, verbose, bootloader, legacy)
