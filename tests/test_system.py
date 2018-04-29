import zedenv.lib.check


def test_zfs_module_loaded():
    assert zedenv.lib.check.zfs_module_loaded()
