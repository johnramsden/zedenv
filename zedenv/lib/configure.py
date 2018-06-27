import pkg_resources
import platform

from zedenv.lib.logger import ZELogger


# Import plugins
def get_plugins():
    # https://packaging.python.org/guides/packaging-namespace-packages/
    # https://packaging.python.org/guides/creating-and-discovering-plugins/

    plugins = {}

    for entry_point in pkg_resources.iter_entry_points('zedenv.plugins'):
        plugins[entry_point.name] = entry_point.load()

    return plugins


def get_bootloader_properties():
    plugins = get_plugins()
    plugin_list = []

    for p in plugins:
        if platform.system().lower() in plugins[p].systems_allowed:
            plugin_list.append({
                "bootloader": plugins[p].bootloader,
                "properties": plugins[p].allowed_properties
            })

    return plugin_list


def get_bootloader(boot_environment: str,
                   old_boot_environment: str,
                   bootloader: str,
                   verbose: bool,
                   noconfirm: bool,
                   noop: bool,
                   be_root: str):
    bootloader_plugin = None
    if bootloader:
        plugins = get_plugins()
        if bootloader in plugins:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": ("Configuring boot environment "
                            f"bootloader with {bootloader}\n")
            }, verbose)
            if platform.system().lower() in plugins[bootloader].systems_allowed:
                try:
                    bootloader_plugin = plugins[bootloader]({
                        'boot_environment': boot_environment,
                        'old_boot_environment': old_boot_environment,
                        'bootloader': bootloader,
                        'verbose': verbose,
                        'noconfirm': noconfirm,
                        'noop': noop,
                        'boot_environment_root': be_root
                    })
                except ValueError as e:
                    ZELogger.log({
                        "level": "EXCEPTION",
                        "message": f"Failed to run plugin {bootloader}\n{e}\n"
                    }, exit_on_error=True)
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
