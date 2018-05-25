import click

import zedenv.plugins.configuration as plugin_config


class FreeBSDLoader:
    systems_allowed = ["freebsd",
                       "linux" # Remove later, for testing
]

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

    def post_activate(self):
        pass

    def pre_activate(self):
        pass

    def mid_activate(self, be_mountpoint: str):
        pass
