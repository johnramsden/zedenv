"""Get boot environment properties cli"""

from typing import Optional

import click

import pyzfscmds.system.agnostic
import pyzfscmds.cmd

import zedenv.lib.be
import zedenv.lib.check
from zedenv.lib.logger import ZELogger


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

    if not scripting:
        ZELogger.log({"level": "INFO", "message": prop_list[0]})

    for p in prop_list:
        split_prop = p.split()
        if split_prop[property_index].startswith("org.zedenv"):
            ZELogger.log({"level": "INFO", "message": p})


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
