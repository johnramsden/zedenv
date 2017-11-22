def mount_dataset(mountpoint):
    """
    Check if 'zfs' mount.
    return root dataset, or None if not found
    """

    with open("/proc/mounts") as f:
        mount = next((ds for ds in f.read().splitlines() if f"{mountpoint} zfs" in ds), None)

    if mount is None:
        root_dataset = None
    else:
        root_dataset = mount.split(" ")[0]

    return root_dataset
