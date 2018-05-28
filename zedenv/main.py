"""
zedenv boot environment manager cli
"""
import os
import signal
import sys
import platform

import click

import zedenv
import zedenv.lib.check
import zedenv.lib.configure

signal.signal(signal.SIGINT, signal.default_int_handler)


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Version {zedenv.__version__}")
    ctx.exit()


def list_plugins(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    plugins = zedenv.lib.configure.get_plugins()

    click.echo("Available plugins:\n")
    for key, value in plugins.items():
        if platform.system().lower() in plugins[key].systems_allowed:
            click.echo(key)

    ctx.exit()


command_modules_folder = os.path.join(os.path.dirname(__file__), 'cli')


class ZECLI(click.MultiCommand):
    """
    Add all commands in cli directory
    """

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(command_modules_folder):
            if filename.endswith('.py') and not filename.startswith('__init__'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(command_modules_folder, name + '.py')
        if not os.path.isfile(fn):
            sys.exit(f"Command '{name}' doesn't exist, run 'zedenv --help'")
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']


@click.command(cls=ZECLI)
@click.option('--version',
              is_flag=True,
              callback=print_version,
              expose_value=False)
@click.option('--plugins',
              help="List available plugins.",
              is_flag=True,
              callback=list_plugins,
              expose_value=False)
# Information on callbacks:
# http://pocco-click.readthedocs.io/en/latest/options.html#callbacks-and-eager-options
def cli():
    """ZFS boot environment manager cli"""

    try:
        zedenv.lib.check.startup_check()
    except RuntimeError as err:
        sys.exit(err)


if __name__ == '__main__':
    cli(prog_name="zedenv")
