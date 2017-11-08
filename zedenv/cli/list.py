"""List boot environments cli"""

import click


@click.command(name="list",
               help="List all boot environments.")
@click.option('--verbose', '-v',
              is_flag=True,
              help="Print verbose output.")
def cli(boot_environment, verbose):
    if verbose:
        click.echo("Listing Boot Environments.")
