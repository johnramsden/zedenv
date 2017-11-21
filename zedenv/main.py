"""
zedenv boot environment manager cli
"""
import os
import signal
import subprocess
import sys

import click
import zedenv
import zedenv.lib.check as ze_check

signal.signal(signal.SIGINT, signal.default_int_handler)


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Version {zedenv.__version__}")
    ctx.exit()


plugin_folder = os.path.join(os.path.dirname(__file__), 'cli')


class ZECLI(click.MultiCommand):

    """
    Add all commands in cli directory
    """

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py') and not filename.startswith('__init__'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugin_folder, name + '.py')
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']


@click.command(cls=ZECLI)
@click.option('--version',
              is_flag=True,
              callback=print_version,
              expose_value=False)
def cli():
    """ZFS boot environment manager cli"""
    try:
        ze_check.startup_check()
    except RuntimeError as err:
        click.echo(f"Startup check failed.")
        sys.exit(err)


if __name__ == '__main__':
    cli(prog_name="zedenv")
