"""Get boot environment properties cli"""

import click
import pyzfscmds.cmd
import pyzfscmds.system.agnostic
import zedenv.configuration
import zedenv.lib.be
import zedenv.lib.check
from typing import Optional, List
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


def zedenv_get(zedenv_properties: Optional[list],
               scripting: Optional[bool],
               recursive: Optional[bool],
               be_root: str):
    property_index = 0
    columns = ["property", "value"]

    zedenv_props = zedenv_properties if zedenv_properties else ["all"]

    if recursive:
        property_index = property_index + 1
        columns.insert(0, "name")

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
    prop_output = []

    if not scripting:
        prop_output.append(prop_list[0].split())

    prop_list_props = []
    for pr in prop_list:
        split_prop = pr.split()
        if split_prop[property_index].startswith("org.zedenv"):
            prop_list_props.append(split_prop)

    prop_output.extend(prop_list_props)

    if not recursive:
        props_unset = []
        only_props = [j[property_index] for j in prop_list_props]
        for cfg in zedenv.configuration.allowed_properties:
            if f'org.zedenv:{cfg["property"]}' not in only_props:
                props_unset.append(
                    [f'org.zedenv:{cfg["property"]}', f'default ({cfg["default"]})'])

        prop_output.extend(props_unset)

    # Set minimum column width to name of column plus one
    widths = [len(l) + 1 for l in columns]

    # Check for largest column entry and use as width.
    for upe in prop_output:
        for i, w in enumerate(upe):
            if len(w) > widths[i]:
                widths[i] = len(w)

    formatted_list_entries = [format_get(b, scripting, widths)
                              for b in prop_output]

    for k in formatted_list_entries:
        ZELogger.log({"level": "INFO", "message": k})


@click.command(name="get",
               help="Get all boot environment properties that are set.")
@click.option('--recursive', '-r',
              is_flag=True,
              help="Recursively get all zedenv properties from all datasets under ROOT.")
@click.option('--scripting', '-H',
              is_flag=True,
              help="Scripting output.")
@click.argument('zedenv_properties', nargs=-1, required=False)
def cli(zedenv_properties: Optional[list],
        scripting: Optional[bool],
        recursive: Optional[bool]):
    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        ZELogger.log({"level": "EXCEPTION", "message": err}, exit_on_error=True)

    zedenv_get(zedenv_properties,
               scripting,
               recursive,
               zedenv.lib.be.root())
