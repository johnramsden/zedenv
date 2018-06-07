import shutil
import os
import re

import click
import zedenv.lib.be
from zedenv.lib.logger import ZELogger

allowed_keys = (
    'boot_environment',
    'old_boot_environment',
    'bootloader',
    'verbose',
    'noconfirm',
    'noop',
    'boot_environment_root'
)


class Plugin(object):

    def __init__(self, zedenv_data: dict):

        for k in zedenv_data:
            if k not in allowed_keys:
                raise ValueError(f"Type {k} is not in allowed keys")

        self.boot_environment = zedenv_data['boot_environment']
        self.old_boot_environment = zedenv_data['old_boot_environment']
        self.bootloader = zedenv_data['bootloader']
        self.verbose = zedenv_data['verbose']
        self.noconfirm = zedenv_data['noconfirm']
        self.noop = zedenv_data['noop']
        self.be_root = zedenv_data['boot_environment_root']

        self.zedenv_properties = {}

    def plugin_property_error(self, prop):
        ZELogger.log({
            "level": "EXCEPTION",
            "message": (f"To use the {self.bootloader} plugin, use default{prop}, or set props\n"
                        f"To set it use the command (replacing with your pool and dataset)\n'"
                        f"zfs set org.zedenv.{self.bootloader}:{prop}='<new mount>' "
                        "zpool/ROOT/default\n")
        }, exit_on_error=True)

    def check_zedenv_properties(self):
        """
        Get zedenv properties in format:
            {"property": <property val>}
        If prop unset, leave default
        """
        for prop in self.zedenv_properties:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Checking prop: 'org.zedenv.{self.bootloader}:{prop}'"
            }, self.verbose)
            prop_val = zedenv.lib.be.get_property(
                    "/".join([self.be_root, self.boot_environment]),
                    f"org.zedenv.{self.bootloader}:{prop}")

            if prop_val is not None and prop_val != "-":
                self.zedenv_properties[prop] = prop_val
                ZELogger.verbose_log({
                    "level": "INFO",
                    "message": (f"org.zedenv.{self.bootloader}:{prop}="
                                f"{self.zedenv_properties[prop]}.\n")
                }, self.verbose)

    def recurse_move(self, source, dest, overwrite=False):
        for tf in os.listdir(source):
            tf_path_src = os.path.join(source, tf)
            tf_path_dst = os.path.join(dest, tf)

            if os.path.isfile(tf_path_src):
                if os.path.isfile(tf_path_dst) and not overwrite:
                    ZELogger.verbose_log({
                        "level": "INFO",
                        "message": f"File {tf_path_dst} already exists, will not modify.\n"
                    }, self.verbose)
                else:
                    try:
                        shutil.copy(tf_path_src, tf_path_dst)
                    except PermissionError:
                        ZELogger.log({
                            "level": "EXCEPTION",
                            "message": f"Require Privileges to write to '{tf_path_dst}.'\n"
                        }, exit_on_error=True)
                    ZELogger.verbose_log({
                        "level": "INFO",
                        "message": f"Copied file {tf_path_src} -> {tf_path_dst}\n"
                    }, self.verbose)
            elif os.path.isdir(tf_path_src):
                if os.path.isdir(tf_path_dst) and not overwrite:
                    ZELogger.verbose_log({
                        "level": "INFO",
                        "message": f"Directory {tf_path_dst} already exists, will not modify.\n"
                    }, self.verbose)

                    # Call again, may be empty
                    self.recurse_move(tf_path_src, tf_path_dst, overwrite=overwrite)

                else:
                    if os.path.isdir(tf_path_dst):
                        shutil.move(tf_path_dst, f"{tf_path_dst}.bak")
                        ZELogger.verbose_log({
                            "level": "INFO",
                            "message": (f"Directory {tf_path_dst} already exists, "
                                        f"creating backup {tf_path_dst}.bak.\n")
                        }, self.verbose)
                    try:
                        shutil.copytree(tf_path_src, tf_path_dst)
                    except PermissionError as e:
                        ZELogger.log({
                            "level": "EXCEPTION",
                            "message": f"Require Privileges to write to {tf_path_dst}\n{e}"
                        }, exit_on_error=True)
                    except IOError as e:
                        ZELogger.log({
                            "level": "EXCEPTION",
                            "message": f"IOError writing to {tf_path_dst}\n{e}"
                        }, exit_on_error=True)
                    ZELogger.verbose_log({
                        "level": "INFO",
                        "message": f"Copied dir {tf_path_src} -> {tf_path_dst}\n"
                    }, self.verbose)

    def modify_fstab(self, be_mountpoint: str, replace_pattern: str, new_entry: str):
        """
        Modify fstab, changing pattern.
        """

        be_fstab = os.path.join(be_mountpoint, "etc/fstab")
        temp_fstab = os.path.join(be_mountpoint, "fstab.zedenv.new")

        try:
            shutil.copy(be_fstab, temp_fstab)
        except PermissionError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Require Privileges to write to {temp_fstab}\n{e}"
            }, exit_on_error=True)
        except IOError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"IOError writing to {temp_fstab}\n{e}"
            }, exit_on_error=True)

        target = re.compile(replace_pattern)

        """
        Find match for: $esp/$env_dir/zedenv-$boot_environment $boot_location <fstab stuff>
        eg: /mnt/efi/env/zedenv-default-3 /boot none  rw,defaults,bind 0 0
        """

        with open(temp_fstab) as in_f:
            lines = in_f.readlines()

            match = next(
                ((i, target.search(m)) for i, m in enumerate(lines) if target.search(m)), None)

        """
        Replace BE name with new one
        """

        if match:
            old_fstab_entry = lines[match[0]]
            new_fstab_entry = re.sub(
                replace_pattern, r"\1" + new_entry + r"\3", lines[match[0]])

            lines[match[0]] = new_fstab_entry

            with open(temp_fstab, 'w') as out_f:
                out_f.writelines(lines)

            ZELogger.log({
                "level": "INFO",
                "message": (f"Replaced fstab entry:\n{old_fstab_entry}\nWith new entry:\n"
                            f"{new_fstab_entry}\nIn the boot environment's "
                            f"'/etc/fstab'.\n")
            })
        else:
            ZELogger.log({
                "level": "INFO",
                "message": (f"Couldn't find bindmounted directory to replace, your system "
                            "may not be configured for boot environments with bindmounted "
                            "'/boot'.")
            })

        if not self.noop:
            try:
                shutil.copy(be_fstab, f"{be_fstab}.bak")
            except PermissionError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Require Privileges to write to {be_fstab}.bak\n{e}"
                }, exit_on_error=True)
            except IOError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"IOError writing to  {be_fstab}.bak\n{e}"
                }, exit_on_error=True)

            if not self.noconfirm:
                if click.confirm(
                        "Would you like to edit the generated 'fstab'?", default=True):
                    click.edit(filename=temp_fstab)

            try:
                shutil.copy(temp_fstab, be_fstab)
            except PermissionError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Require Privileges to write to {be_fstab}\n{e}"
                }, exit_on_error=True)
            except IOError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"IOError writing to {be_fstab}\n{e}"
                }, exit_on_error=True)

            ZELogger.log({
                "level": "INFO",
                "message": (f"Moved new '/etc/fstab' into place. A copy of the original "
                            "'/etc/fstab' can be found at '/etc/fstab.bak'.\n")
            })

    def post_activate(self):
        pass

    def pre_activate(self):
        pass

    def mid_activate(self, be_mountpoint: str):
        pass
