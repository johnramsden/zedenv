"""
Set boot environment properties cli
"""

import click
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
from typing import Optional, List, Dict

import zedenv.configuration
import zedenv.lib.be
import zedenv.lib.check
import zedenv.lib.configure
from zedenv.lib.logger import ZELogger


def format_get(get_line: list,
               scripting: Optional[bool],
               widths: List[int]) -> str:
    """
    Formats list into column separated string with tabs if scripting.
    """
    if scripting:
        return "\t".join(get_line)
    else:
        fmt_line = ["{{: <{width}}}".format(width=(w + 1)) for w in widths]
        return " ".join(fmt_line).format(*get_line)


def get_set_properties(property_index: int,
                       props: Optional[list],
                       recursive: Optional[bool]) -> List[Dict]:
    """
    Get currently set zedenv props and return a list of dicts as:
    [{ "property": ..., "value": ..., "name": ...}]
    """
    prop_table = []
    for pl in props:
        split_prop = pl.split()

        if split_prop[property_index].startswith("org.zedenv"):

            prop_dict = {
                "property": split_prop[property_index],
                "value": split_prop[property_index + 1]
            }

            if recursive:
                prop_dict["name"] = split_prop[0]

            prop_table.append(prop_dict)

    return prop_table


def zedenv_get(zedenv_properties: Optional[list],
               scripting: Optional[bool],
               recursive: Optional[bool],
               defaults: Optional[bool],
               be_root: str):
    set_properties = []
    if not defaults:
        # Get currently set zedenv props
        property_index = 0
        columns = ["property", "value"]

        zedenv_props = zedenv_properties if zedenv_properties else ["all"]

        if recursive:
            property_index = property_index + 1
            columns.insert(0, "name")  # Include dataset if recursive

        props = None
        try:
            props = pyzfscmds.cmd.zfs_get(be_root,
                                          properties=zedenv_props,
                                          scripting=scripting,
                                          recursive=recursive,
                                          columns=columns,
                                          zfs_types=['filesystem'])
        except RuntimeError as err:
            ZELogger.log({
                "level": "EXCEPTION",
                "message": f"Failed to get zedenv properties\n{err}\n"
            }, exit_on_error=True)

        prop_list = props.splitlines()

        if not scripting:
            set_properties.append(prop_list[0].split())  # Title

        set_properties_dicts = get_set_properties(property_index, prop_list, recursive)

        # Add properties that are currently set
        for item in set_properties_dicts:
            line = []
            if recursive:
                line.append(item["name"])
            line.extend([item["property"], item["value"]])
            set_properties.append(line)

    else:
        set_properties.append(["PROPERTY", "DEFAULT", "DESCRIPTION"])
        # Print defaults for regular properties
        for cfg in zedenv.configuration.allowed_properties:
            if zedenv_properties:
                if f'org.zedenv:{cfg["property"]}' in zedenv_properties:
                    set_properties.append(
                        [f'org.zedenv:{cfg["property"]}', cfg['default'], cfg['description']])
            else:
                set_properties.append(
                    [f'org.zedenv:{cfg["property"]}', cfg['default'], cfg['description']])

        # Print defaults for bootloader properties
        for bl in zedenv.lib.configure.get_bootloader_properties():
            for pcfg in bl['properties']:
                if zedenv_properties:
                    if f'org.zedenv.{bl["bootloader"]}:{pcfg["property"]}' in zedenv_properties:
                        set_properties.append([
                            f'org.zedenv.{bl["bootloader"]}:{pcfg["property"]}',
                            pcfg['default'],
                            pcfg['description']
                        ])
                else:
                    set_properties.append([
                        f'org.zedenv.{bl["bootloader"]}:{pcfg["property"]}',
                        pcfg['default'],
                        pcfg['description']
                    ])

    # Set minimum column width to name of column plus one
    widths = [len(l) + 1 for l in set_properties[0]]

    # Check for largest column entry and use as width.
    for upe in set_properties:
        for i, w in enumerate(upe):
            if len(w) > widths[i]:
                widths[i] = len(w)

    formatted_list_entries = [format_get(b, scripting, widths)
                              for b in set_properties]

    return formatted_list_entries


@click.command(name="get",
               help="Print boot environment properties.")
@click.option('--recursive', '-r',
              is_flag=True,
              help="Recursively get all zedenv properties from all datasets under ROOT.")
@click.option('--scripting', '-H',
              is_flag=True,
              help="Scripting output.")
@click.option('--defaults', '-D',
              is_flag=True,
              help="Show default settings only.")
@click.argument('zedenv_properties', nargs=-1, required=False)
def cli(zedenv_properties: Optional[list],
        scripting: Optional[bool],
        recursive: Optional[bool],
        defaults: Optional[bool]):

    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)

    formatted_list_entries = zedenv_get(zedenv_properties,
                                        scripting,
                                        recursive,
                                        defaults,
                                        zedenv.lib.be.root())

    for k in formatted_list_entries:
        ZELogger.log({"level": "INFO", "message": k})
