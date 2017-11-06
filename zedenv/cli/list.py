"""List boot environments cli"""

import click


@click.command(name="list",
               help="List all boot environments.")
@click.option('--verbose',
              is_flag=True,
              help="Print verbose output.")
@click.argument('bootenvironment')
def cli(bootenvironment, verbose):
    if verbose:
        click.echo("Listing Boot Environments.")
        
    if bootenvironment:
        click.echo(bootenvironment)
