import pytest
import datetime

from zedenv.lib.zfs.command import ZFS


"""zfs commands tests"""

require_root_dataset = pytest.mark.require_root_dataset


@pytest.mark.parametrize("recursive", [True, False])
@pytest.mark.parametrize("depth", [None, 0, 1])
@pytest.mark.parametrize("scripting", [True, False])
@pytest.mark.parametrize("parsable", [True, False])
@pytest.mark.parametrize("columns", [
        None, ["name"], ["name", "property", "value", "received", "source"],
        # ["name"], ["property"], ["value"], ["received"], ["source"],
        # ["name", "property", "value", "source"]
    ])
@pytest.mark.parametrize("zfs_types",  [
        None, [], ["all"], ["filesystem", "snapshot"]
        # ["filesystem"], ["snapshot"], ["volume"]
    ])
@pytest.mark.parametrize("source", [
        None, [], ["local"],
        ["local", "default", "inherited", "temporary", "received", "none"],
        # ["default"], ["inherited"], ["temporary"], ["received"], ["none"]
    ])
@pytest.mark.parametrize("properties", [
        None, ["all"], ["mountpoint", "canmount"]
    ])
@require_root_dataset
def test_zfs_get_successful(root_dataset, recursive, depth, scripting,
                            parsable, columns, zfs_types, source, properties):
    """ Test will pass if get successful"""
    ZFS.get(root_dataset,
            recursive=recursive,
            depth=depth,
            scripting=scripting,
            parsable=parsable,
            columns=columns,
            zfs_types=zfs_types,
            source=source,
            properties=properties)

# Incorrect options to test
@pytest.mark.parametrize(
    "columns,zfs_types,source,properties", [
        # Test incorrect columns
        (["fakecolumn"],                     ["all"], ["local"], ["all"]),
        (["fakecolumnone", "fakecolumntwo"], ["all"], ["local"], ["all"]),
        ("notalist",                         ["all"], ["local"], ["all"]),
        # Test incorrect zfs_types
        (["name"],                           ["notatype"], ["local"], ["all"]),
        (["name"],                           "notalist",   ["local"], ["all"]),
        # Test incorrect source
        (["name"], ["all"],                  ["notasource"], ["all"]),
        (["name"], ["all"],                  "notalist",     ["all"]),
        # Test incorrect properties
        (["name"], ["all"],                  ["local"], ["notaprop"]),
        (["name"], ["all"],                  ["local"], "notalist"),
    ])
# Acceptable options
@pytest.mark.parametrize("recursive", [True, False])
@pytest.mark.parametrize("depth",     [None, 0, 1])
@pytest.mark.parametrize("scripting", [True, False])
@pytest.mark.parametrize("parsable",  [True, False])
@require_root_dataset
def test_zfs_get_fails(root_dataset, recursive, depth, scripting,
                       parsable, columns, zfs_types, source, properties):
    """ Test will fail if get unsuccessful"""
    with pytest.raises(RuntimeError):
        ZFS.get(root_dataset,
                recursive=recursive,
                depth=depth,
                scripting=scripting,
                parsable=parsable,
                columns=columns,
                zfs_types=zfs_types,
                source=source,
                properties=properties)
