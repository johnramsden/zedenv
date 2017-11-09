"""List boot environments cli"""

import datetime

import click
import zedenv.lib.zfs as zfslib

@click.command(name="create",
               help="Create a boot environment.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
@click.option('--existing', '-e',
              is_flag=True,
              help="Use existing boot environment as source.")
@click.argument('boot_environment')
def cli(boot_environment, verbose, existing):

    if verbose:
        click.echo("Listing Boot Environments verbosely.")

    zfs = zfslib.ZFS()

    root_dataset = "zpool/ROOT/default" # TODO: Get dynamically

    click.echo("Cloning...")
    if existing:
        source_snap = existing
    else:
        snap_suffix = "zedenv-{}".format(datetime.datetime.now().isoformat())
        zfs.snapshot(root_dataset, snap_suffix)
        source_snap = f"{root_dataset}@{snap_suffix}"

    print(f"Using {source_snap} as source")
    try:
        zfs.clone(source_snap, boot_environment)
    except RuntimeError as rte:
        click.echo(f"Failed to create {boot_environment} from {source_snap}")
        click.echo(f"Error: {rte}")
