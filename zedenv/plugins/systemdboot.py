import shutil
import os
import re
import tempfile

import click

import zedenv.lib.be
import zedenv.lib.system
from zedenv.lib.logger import ZELogger


class SystemdBoot:
    systems_allowed = ["linux"]

    def __init__(self, boot_environment: str,
                 old_boot_environment: str,
                 bootloader: str,
                 verbose: bool = False,
                 noconfirm: bool = False,
                 noop: bool = False):
        self.boot_environment = boot_environment
        self.old_boot_environment = old_boot_environment
        self.bootloader = bootloader
        self.verbose = verbose
        self.noconfirm = noconfirm
        self.noop = noop
        self.be_root = zedenv.lib.be.root()

        self.env_dir = "env"
        self.boot_mountpoint = "/boot"

        self.entry_prefix = "zedenv"

        self.old_entry = f"{self.entry_prefix}-{self.old_boot_environment}"
        self.new_entry = f"{self.entry_prefix}-{self.boot_environment}"

        esp = zedenv.lib.be.get_property(
                    "/".join([self.be_root, boot_environment]), "org.zedenv:esp")
        if esp is None or esp == "-":
            self.esp = "/mnt/efi"
        else:
            self.esp = esp
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"esp set to {esp}\n"
        }, verbose)

        if not os.path.isdir(self.esp):
            ZELogger.log({
                "level": "EXCEPTION",
                "message": ("To use the systemdboot plugin, an 'esp' must be mounted at the "
                            "default location of `/mnt/esp`, or at another location, with the "
                            "property 'org.zedenv:esp' set on the dataset. To set it use the "
                            "command (replacing with your pool and dataset)\n'"
                            "zfs set org.zedenv:esp='/mnt/efi' zpool/ROOT/default\n")
            }, exit_on_error=True)

    def modify_fstab(self, be_mountpoint: str):

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

        replace_pattern = r'(^{esp}/{env}/?)(.*)(\s.*{boot}\s.*$)'.format(
            esp=self.esp, env=self.env_dir, boot=self.boot_mountpoint)

        target = re.compile(replace_pattern)

        """
        Find match for: $esp/$env_dir/$boot_environment $boot_location <fstab stuff>
        eg: /mnt/efi/env/default-3 /boot none  rw,defaults,bind 0 0
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
                replace_pattern, r"\1" + self.new_entry + r"\3", lines[match[0]])

            lines[match[0]] = new_fstab_entry

            with open(temp_fstab, 'w') as out_f:
                out_f.writelines(lines)
        else:
            ZELogger.log({
                "level": "INFO",
                "message": (f"Couldn't find bindmounted directory to replace, your system "
                            "may not be configured for boot environments with systemdboot.")
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
                "message": (f"Replaced fstab entry:\n{old_fstab_entry}\nWith new entry:\n"
                            f"{new_fstab_entry}\nIn the boot environment's "
                            f"'/etc/fstab'. A copy of the original "
                            "'/etc/fstab' can be found at '/etc/fstab.bak'.\n")
            })

    def edit_bootloader_entry(self, temp_esp: str):
        temp_entries_dir = os.path.join(temp_esp, "loader/entries")
        temp_bootloader_file = os.path.join(temp_entries_dir,
                                            f"{self.new_entry}.conf")

        real_entries_dir = os.path.join(self.esp, "loader/entries")
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
                          if en.split(".conf")[0] == (
                                  self.old_entry or self.new_entry)]

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

    def modify_bootloader(self, temp_esp: str,):

        real_kernel_dir = os.path.join(self.esp, "env")
        temp_kernel_dir = os.path.join(temp_esp, "env")

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

        if os.path.isdir(temp_new_dataset_kernel):
            ZELogger.log({
                "level": "INFO",
                "message": (f"New kernel directory {temp_new_dataset_kernel} already exists. "
                            f"Wont modify.\n")
            }, self.verbose)

    def edit_bootloader_default(self, temp_esp: str, overwrite: bool):
        real_loader_dir_path = os.path.join(self.esp, "loader")
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

    def recurse_move(self, source, dest):
        for tf in os.listdir(source):
            tf_path_src = os.path.join(source, tf)
            tf_path_dst = os.path.join(dest, tf)

            if os.path.isfile(tf_path_src):
                if os.path.isfile(tf_path_dst):
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
                            "message": (f"Require Privileges to write to "
                                        f"'{tf_path_dst}.bak'\n")

                        }, exit_on_error=True)
                        ZELogger.verbose_log({
                            "level": "INFO",
                            "message": f"Copied file {tf_path_src} -> {tf_path_dst}\n"
                        }, self.verbose)
            elif os.path.isdir(tf_path_src):
                if os.path.isdir(tf_path_dst):
                    ZELogger.verbose_log({
                        "level": "INFO",
                        "message": f"Directory {tf_path_dst} already exists, will not modify.\n"
                    }, self.verbose)

                    # Call again, may be empty
                    self.recurse_move(tf_path_src, tf_path_dst)

                else:
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

            self.recurse_move(t_esp, self.esp)

            self.edit_bootloader_default(t_esp, overwrite=True)

        # self.cleanup_entries()

    def pre_activate(self):
        pass

    def mid_activate(self, be_mountpoint: str):
        ZELogger.verbose_log({
            "level": "INFO",
            "message": f"Running {self.bootloader} mid activate.\n"
        }, self.verbose)
        self.modify_fstab(be_mountpoint)
