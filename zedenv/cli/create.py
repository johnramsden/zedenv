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
    created_snap = "zpool/ROOT/default-test-2017-09-17-192524@bez-be-snap-2017-09-17"

    if verbose:
        click.echo("Listing Boot Environments verbosely.")

    ZFS = libzfs.ZFS()

    click.echo("Cloning...")
    if existing:
        source_snap = existing
    else:
        source_snap = created_snap

    print("Using ", source_snap, " as source")
    try:
        ZFS.clone(source_snap, boot_environment)
    except RuntimeError as rte:
        click.echo("Failed to create {}".format(boot_environment))
        if verbose:
            click.echo("Error: {}".format(rte))
