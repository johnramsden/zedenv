
class SystemdBoot:

    def __init__(self, boot_environment: str,
                 bootloader: str, verbose: bool, legacy: bool):
        self.boot_environment = boot_environment
        self.bootloader = bootloader
        self.verbose = verbose
        self.legacy = legacy

    def activate(self):
        return f"Registered systemdboot plugin for boot env: {self.boot_environment}"
