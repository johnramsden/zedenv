import os
import re
import shutil

import pyzfscmds.cmd

import zedenv.plugins.configuration as plugin_config
from zedenv.lib.logger import ZELogger


class FreeBSDLoader:
    systems_allowed = ["freebsd"]

    def __init__(self, zedenv_data: dict):

        for k in zedenv_data:
            if k not in plugin_config.allowed_keys:
                raise ValueError(f"Type {k} is not in allowed keys")

        self.boot_environment = zedenv_data['boot_environment']
        self.old_boot_environment = zedenv_data['old_boot_environment']
        self.bootloader = zedenv_data['bootloader']
        self.verbose = zedenv_data['verbose']
        self.noconfirm = zedenv_data['noconfirm']
        self.noop = zedenv_data['noop']
        self.be_root = zedenv_data['boot_environment_root']

        self.zpool_cache = "boot/zfs/zpool.cache"
        self.zfs_be_path = "etc/rc.d/zfsbe"
        self.loader_config = {
            "system": "boot/loader.conf",
            "local": "boot/loader.conf.local",
        }

        self.zfs_be = False

    def post_activate(self):
        canmount_setting = "canmount=noauto" if self.zfs_be else "canmount=on"

        try:
            pyzfscmds.cmd.zfs_set(f"{self.be_root}/{self.boot_environment}", canmount_setting)
        except RuntimeError:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to set {canmount_setting} for {ds}\n{e}\n"
            }, exit_on_error=True)

    def pre_activate(self):
        pass

    def _loader_replace(self, configs: list):
        be_dataset = f"{self.be_root}/{self.boot_environment}"

        target = re.compile(r'^vfs.root.mountfrom=.*$')

        for c in configs:
            with open(c, "r") as loader_conf:
                conf_list = loader_conf.readlines()

            line_nums = [l for l, val in enumerate(conf_list) if target.search(val)]

            for lnum in line_nums:
                conf_list[lnum] = f"vfs.root.mountfrom={be_dataset}\n"

            if not self.noop:
                if os.path.isfile(c):
                    ZELogger.verbose_log({
                        "level": "INFO",
                        "message": (f"File {c} already exists, backed up to "
                                    f"'{c}.bak' and replaced.\n")
                    }, self.verbose)
                    if os.path.isfile(f"{c}.bak"):
                        try:
                            os.remove(f"{c}.bak")
                        except PermissionError:
                            ZELogger.log({
                                "level": "EXCEPTION",
                                "message": (f"Require Privileges to remove "
                                            f"'{c}.bak'\n")
                            }, exit_on_error=True)
                    try:
                        shutil.move(c, f"{c}.bak")
                    except PermissionError:
                        ZELogger.log({
                            "level": "EXCEPTION",
                            "message": (f"Require Privileges to write to "
                                        f"'{c}.bak'\n")
                        }, exit_on_error=True)

                with open(c, "w") as loader_conf:
                    loader_conf.writelines(conf_list)

    def mid_activate(self, be_mountpoint: str):
        # System bootloader config must exist
        system_loader_config = os.path.join(be_mountpoint, self.loader_config['system'])
        if not os.path.isfile(system_loader_config):
            raise RuntimeWarning("System bootloader config does not exist.\n")

        loader_configs = [system_loader_config]

        self.zfs_be = True if os.path.isfile(
            os.path.join(be_mountpoint, self.zfs_be_path)) else False

        temp_zpool_cache_path = os.path.join(be_mountpoint, self.zpool_cache)
        system_zpool_cache_path = os.path.join("/", self.zpool_cache)

        if os.path.isfile(system_zpool_cache_path):
            try:
                shutil.copy(system_zpool_cache_path, temp_zpool_cache_path)
            except PermissionError as e:
                raise RuntimeError(
                    f"Require Privileges to write to '{temp_zpool_cache_path}'\n{e}")
            except IOError as e:
                raise RuntimeWarning(f"IO Error writing to '{temp_zpool_cache_path}'\n{e}")
        else:
            try:
                os.remove(temp_zpool_cache_path)
            except PermissionError as e:
                raise RuntimeError(
                    f"Require Privileges to write to '{temp_zpool_cache_path}'\n{e}")
            except IOError as e:
                raise RuntimeWarning(f"IO Error writing to '{temp_zpool_cache_path}'\n{e}")

        local_loader_config = os.path.join(be_mountpoint, self.loader_config['local'])
        if os.path.isfile(local_loader_config):
            loader_configs.append(local_loader_config)

        self._loader_replace(loader_configs)
