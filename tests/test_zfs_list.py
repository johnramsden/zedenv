import pytest
import datetime

import zedenv.lib.zfs.utility as zfs_utility
from zedenv.lib.zfs.command import ZFS


"""zfs commands tests"""

require_root_dataset = pytest.mark.require_root_dataset


@pytest.mark.parametrize("recursive", [True, False])
@pytest.mark.parametrize("depth",     [None, 0, 1])
@pytest.mark.parametrize("scripting", [True, False])
@pytest.mark.parametrize("parsable",  [True, False])
@pytest.mark.parametrize("columns", [
        None, ["name"], ["name", "used", "available", "referenced", "mountpoint"],
    ])
@pytest.mark.parametrize("zfs_types",  [
        None, [], ["all"], ["filesystem", "snapshot"]
    ])
@pytest.mark.parametrize("sort_properties_ascending",  [None, [], ["compression"]])
@pytest.mark.parametrize("sort_properties_descending", [None, [], ["compression"]])
@require_root_dataset
def test_zfs_list_successful(root_dataset, recursive, depth, scripting, parsable, columns,
                             zfs_types, sort_properties_ascending, sort_properties_descending):
    """ Test will pass if list successful"""

    """
    zfs list [-r|-d depth] [-Hp] [-o property[,property]...]
        [-t type[,type]...] [-s property]... [-S property]...
        filesystem|volume|snapshot
    """
    ZFS.list(root_dataset,
             recursive=recursive,
             depth=depth,
             scripting=scripting,
             parsable=parsable,
             columns=columns,
             zfs_types=zfs_types,
             sort_properties_ascending=sort_properties_ascending,
             sort_properties_descending=sort_properties_descending)


# Incorrect options to test
@pytest.mark.parametrize(
    "columns,zfs_types,sort_properties_ascending,sort_properties_descending", [
        # Test incorrect columns
        (['fakecolumn'], ['all'], ['compression'], ['compression']),
        (['fakecolumnone', 'fakecolumntwo'], ['all'], ['compression'], ['compression']),
        ('notalist',  ['all'], ['compression'], ['compression']),
        # Test incorrect zfs_types
        (['name'], ['notatype'], ['compression'], ['compression']),
        (['name'], 'notalist', ['compression'], ['compression']),
        # Test incorrect sortproperties ascending
        (['name'], ['all'], ['notaprop'], ['compression']),
        (['name'], ['all'], 'notalist', ['compression']),
        # Test incorrect sortproperties descending
        (['name'], ['all'], ['compression'], ['notaprop']),
        (['name'], ['all'], ['compression'], 'notalist'),
    ])
# Acceptable options
@pytest.mark.parametrize("recursive", [True, False])
@pytest.mark.parametrize("depth",     [None, 0, 1])
@pytest.mark.parametrize("scripting", [True, False])
@pytest.mark.parametrize("parsable",  [True, False])
@require_root_dataset
def test_zfs_list_fails(root_dataset, recursive, depth, scripting, parsable, columns,
                        zfs_types, sort_properties_ascending, sort_properties_descending):

    with pytest.raises(RuntimeError):
        ZFS.list(root_dataset,
                 recursive=recursive,
                 depth=depth,
                 scripting=scripting,
                 parsable=parsable,
                 columns=columns,
                 zfs_types=zfs_types,
                 sort_properties_ascending=sort_properties_ascending,
                 sort_properties_descending=sort_properties_descending)
