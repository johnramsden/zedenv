"""List boot environments cli"""

import click
import zedenv.lib.zfs as libzfs


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

    # TODO: Get source dataset
    source_snap = "zpool/ROOT/default@fakesnap"
    src_properties = ["acltype=posixacls"]

    if verbose:
        click.echo("Listing Boot Environments verbosely.")

    ZFS = libzfs.ZFS()

    click.echo("Cloning...")
    if existing:
        print("Using ", existing, " as source")
        ZFS.clone(existing, boot_environment)
    else:
        print("Using ", source_snap, " as source")
        ZFS.clone(source_snap, boot_environment, properties=src_properties)
