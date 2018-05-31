import shutil
import os

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
        pass

    def pre_activate(self):
        pass

    def mid_activate(self, be_mountpoint: str):
        pass
