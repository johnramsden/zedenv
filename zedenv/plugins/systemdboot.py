import click
import os
import shutil
import tempfile
import zedenv.plugins.configuration as plugin_config
from typing import Tuple
from zedenv.lib.logger import ZELogger


class SystemdBoot(plugin_config.Plugin):
    systems_allowed = ["linux"]
    bootloader = "systemdboot"

    allowed_properties: Tuple[dict] = (
        {
            "property": f"esp",
            "description": "Set location for esp.",
            "default": "/mnt/efi"
        },
    )

    def __init__(self, zedenv_data: dict):

        super().__init__(zedenv_data)

        self.env_dir = "env"
        self.boot_mountpoint = "/boot"

        self.entry_prefix = "zedenv"

        self.old_entry = f"{self.entry_prefix}-{self.old_boot_environment}"
        self.new_entry = f"{self.entry_prefix}-{self.boot_environment}"

        # Set defaults
        for pr in self.allowed_properties:
            self.zedenv_properties[pr["property"]] = pr["default"]

        self.check_zedenv_properties()

        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"esp set to {self.zedenv_properties['esp']}\n"
        }, self.verbose)

        if not os.path.isdir(self.zedenv_properties["esp"]):
            self.plugin_property_error(self.zedenv_properties)

    def edit_bootloader_entry(self, temp_esp: str):
        temp_entries_dir = os.path.join(temp_esp, "loader/entries")
        temp_bootloader_file = os.path.join(temp_entries_dir,
                                            f"{self.new_entry}.conf")

        real_entries_dir = os.path.join(self.zedenv_properties["esp"], "loader/entries")
        real_bootloader_file = os.path.join(
            real_entries_dir, f"{self.old_entry}.conf")

        try:
            os.makedirs(temp_entries_dir)
        except PermissionError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Require Privileges to write to {temp_entries_dir}\n{e}"
            }, exit_on_error=True)
        except OSError as os_err:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": os_err
            }, exit_on_error=True)

        config_entries = os.listdir(real_entries_dir)
        entry_guess_list = [
            f"title   Boot Environment [{self.boot_environment}]\n",
            f"linux           /env/{self.new_entry}/vmlinuz-linux\n",
            f"initrd          /env/{self.new_entry}/initramfs-linux.img\n",
            f"options         zfs={self.be_root}/{self.boot_environment}\n"
        ]

        config_matches = [en.split(".conf")[0] for en in config_entries
                          if en.split(".conf")[0] == (self.old_entry or self.new_entry)]

        old_conf = True if self.old_entry in config_matches else False
        new_conf = True if self.new_entry in config_matches else False

        if old_conf and (self.old_boot_environment == self.boot_environment):
            ZELogger.log({
                "level": "INFO",
                "message": (f"Attempting to activate same boot environment while config "
                            f"'{self.old_entry}.conf' "
                            "already exists. Will not modify old configuration.\n")
            })
        elif new_conf:
            ZELogger.log({
                "level": "INFO",
                "message": (f"Attempting to activate boot environment while config for "
                            f"'{self.new_entry}.conf' already exists. "
                            "Will not modify old configuration.\n")
            })
        else:
            if old_conf:
                ZELogger.log({
                    "level": "INFO",
                    "message": (f"Using existing entry {self.old_entry} as template "
                                f"taking best guess at creating one at "
                                f"{self.new_entry}.conf\n")
                })

                with open(real_bootloader_file, "r") as old_conf:
                    old_conf_list = old_conf.readlines()

                new_entry_list = [l.replace(self.old_boot_environment, self.boot_environment)
                                  for l in old_conf_list]

            else:
                entry_guess_full = '\n'.join(entry_guess_list)
                ZELogger.log({
                    "level": "INFO",
                    "message": (f"You have no matching bootloader entries in {real_entries_dir}, "
                                f"taking best guess at creating one at {real_bootloader_file}:\n"
                                f"{entry_guess_full}.\n")
                })

                new_entry_list = entry_guess_list

            if not self.noop:
                with open(temp_bootloader_file, "w") as boot_conf:
                    boot_conf.writelines(new_entry_list)

                if not self.noconfirm:
                    if click.confirm(
                            "Would you like to edit the generated bootloader config?",
                            default=True):
                        click.edit(filename=temp_bootloader_file)

    def modify_bootloader(self, temp_esp: str, ):

        real_kernel_dir = os.path.join(self.zedenv_properties["esp"], self.env_dir)
        temp_kernel_dir = os.path.join(temp_esp, self.env_dir)

        real_old_dataset_kernel = os.path.join(real_kernel_dir, self.old_entry)
        temp_new_dataset_kernel = os.path.join(temp_kernel_dir, self.new_entry)

        if not os.path.isdir(real_old_dataset_kernel):
            ZELogger.log({
                "level": "INFO",
                "message": (f"No directory for Boot environments kernels found at "
                            f"'{real_old_dataset_kernel}', creating empty directory."
                            f"Don't forget to add your kernel to "
                            f"{real_kernel_dir}/{self.boot_environment}.")
            })
            if not self.noop:
                try:
                    os.makedirs(temp_new_dataset_kernel)
                except PermissionError as e:
                    ZELogger.log({
                        "level": "EXCEPTION",
                        "message": f"Require Privileges to write to {temp_new_dataset_kernel}\n{e}"
                    }, exit_on_error=True)
                except OSError as os_err:
                    ZELogger.log({
                        "level": "EXCEPTION",
                        "message": os_err
                    }, exit_on_error=True)
        else:
            if not self.noop:
                try:
                    shutil.copytree(real_old_dataset_kernel, temp_new_dataset_kernel)
                except PermissionError as e:
                    ZELogger.log({
                        "level": "EXCEPTION",
                        "message": f"Require Privileges to write to {temp_new_dataset_kernel}\n{e}"
                    }, exit_on_error=True)
                except IOError as e:
                    ZELogger.log({
                        "level": "EXCEPTION",
                        "message": f"IOError writing to {temp_new_dataset_kernel}\n{e}"
                    }, exit_on_error=True)

    def edit_bootloader_default(self, temp_esp: str, overwrite: bool):
        real_loader_dir_path = os.path.join(self.zedenv_properties["esp"], "loader")
        temp_loader_dir_path = os.path.join(temp_esp, "loader")

        real_loader_conf_path = os.path.join(real_loader_dir_path, "loader.conf")
        temp_loader_conf_path = os.path.join(temp_loader_dir_path, "loader.conf")

        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Updating {real_loader_conf_path}\n"
        }, self.verbose)

        if not os.path.isdir(temp_loader_dir_path):
            try:
                os.makedirs(temp_loader_dir_path)
            except PermissionError as e:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": f"Require Privileges to write to {temp_loader_dir_path}\n{e}"
                }, exit_on_error=True)
            except OSError as os_err:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": os_err
                }, exit_on_error=True)

        if not os.path.isfile(real_loader_conf_path):
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Missing file: {real_loader_conf_path}\n"
            }, exit_on_error=True)

        try:
            shutil.copy(real_loader_conf_path, temp_loader_conf_path)
        except PermissionError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Require Privileges to write to '{temp_loader_conf_path}'\n{e}"
            }, exit_on_error=True)
        except IOError as e:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"IOError writing to '{temp_loader_conf_path}'\n{e}"
            }, exit_on_error=True)

        with open(temp_loader_conf_path, "r") as loader_conf:
            conf_list = loader_conf.readlines()

        line_num = next((l for l, val in enumerate(conf_list)
                         if val.split(' ', 1)[0] == "default"), None)

        if line_num:
            conf_list[line_num] = f"default    {self.new_entry}\n"

        if not self.noop:
            if os.path.isfile(real_loader_conf_path):
                ZELogger.verbose_log({
                    "level": "INFO",
                    "message": (f"File {real_loader_conf_path} already exists, backed up to "
                                f"'{real_loader_conf_path}.bak' and replaced.\n")
                }, self.verbose)
                if os.path.isfile(f"{real_loader_conf_path}.bak"):
                    try:
                        os.remove(f"{real_loader_conf_path}.bak")
                    except PermissionError:
                        ZELogger.log({
                            "level": "EXCEPTION",
                            "message": (f"Require Privileges to remove "
                                        f"'{real_loader_conf_path}.bak'\n")

                        }, exit_on_error=True)
                try:
                    shutil.move(real_loader_conf_path, f"{real_loader_conf_path}.bak")
                except PermissionError:
                    ZELogger.log({
                        "level": "EXCEPTION",
                        "message": (f"Require Privileges to write to "
                                    f"'{real_loader_conf_path}.bak'\n")

                    }, exit_on_error=True)

            with open(real_loader_conf_path, "w") as loader_conf:
                loader_conf.writelines(conf_list)

            if not self.noconfirm:
                if click.confirm(
                        "Would you like to edit the generated 'loader.conf'?", default=True):
                    click.edit(filename=real_loader_conf_path)

    def post_activate(self):
        ZELogger.verbose_log({
            "level": "INFO",
            "message": (f"Creating Temporary working directory. "
                        "No changes will be made until the end of "
                        "the systemd-boot configuration.\n")
        }, self.verbose)

        with tempfile.TemporaryDirectory(prefix="zedenv", suffix=self.bootloader) as t_esp:
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Created {t_esp}.\n"
            }, self.verbose)

            self.modify_bootloader(t_esp)

            self.edit_bootloader_entry(t_esp)

            self.recurse_move(t_esp, self.zedenv_properties["esp"])

            self.edit_bootloader_default(t_esp, overwrite=True)

        # TODO: self.cleanup_entries()

    def mid_activate(self, be_mountpoint: str):
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Running {self.bootloader} mid activate.\n"
        }, self.verbose)

        replace_pattern = r'(^{esp}/{env}/?)(.*)(\s.*{boot}\s.*$)'.format(
            esp=self.zedenv_properties["esp"], env=self.env_dir, boot=self.boot_mountpoint)

        self.modify_fstab(be_mountpoint, replace_pattern, self.new_entry)

    def post_destroy(self, target):
        real_kernel_dir = os.path.join(self.zedenv_properties["esp"], self.env_dir)
        dataset_kernels = os.path.join(real_kernel_dir, f"{self.entry_prefix}-{target}")

        # if not self.noop:
        if os.path.exists(dataset_kernels):
            shutil.rmtree(dataset_kernels)
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Removed {dataset_kernels}.\n"
            }, self.verbose)

        real_entries_dir = os.path.join(self.zedenv_properties["esp"], "loader/entries")
        real_bootloader_file = os.path.join(real_entries_dir, f"zedenv-{target}.conf")

        if os.path.isfile(real_bootloader_file):
            try:
                os.remove(real_bootloader_file)
            except PermissionError:
                ZELogger.log({
                    "level": "EXCEPTION",
                    "message": (f"Require Privileges to remove "
                                f"'{real_bootloader_file}'\n")

                }, exit_on_error=True)
            ZELogger.verbose_log({
                "level": "INFO",
                "message": f"Removed {real_bootloader_file}.\n"
            }, self.verbose)
