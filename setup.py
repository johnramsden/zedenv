from setuptools import Command, setup
from os.path import abspath, dirname, join
from subprocess import call

from zedenv import __version__

this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()


class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test', '--cov=zedenv', '--cov-report=term-missing'])
        raise SystemExit(errno)

setup(
    name='zedenv',
    version=__version__,
    description='ZFS boot environment manager',
    long_description=long_description,
    url='http://github.com/johnramsden/zedenv',
    author='John Ramsden',
    author_email='johnramsden@riseup.net',
    license='BSD-3-Clause',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'License :: OSI Approved :: BSD License',
      'Programming Language :: Python :: 3.6',
    ],
    keywords = 'cli',
    packages=['zedenv'],
    install_requires=['click'],
    extras_require={
            'test': ['coverage', 'pytest', 'pytest-cov'],
        },
    entry_points={
        'console_scripts': [
            'zedenv=zedenv.main:cli',
        ],
    },
)