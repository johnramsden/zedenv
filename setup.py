from setuptools import setup, find_packages
from os.path import abspath, dirname, join
from subprocess import call

from zedenv.main import __version__

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='zedenv',
    version=__version__,
    description='ZFS boot environment manager',
    long_description=readme(),
    url='http://github.com/johnramsden/zedenv',
    author='John Ramsden',
    author_email='johnramsden@riseup.net',
    license='BSD-3-Clause',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'License :: OSI Approved :: BSD License',
      'Programming Language :: Python :: 3.6',
    ],
    keywords='cli',
    packages=find_packages(exclude=["tests"]),
    install_requires=['click'],
    extras_require={
        'test': [
            'coverage', 'pytest', 'pytest-cov',
        ],
    },
    entry_points={
        'console_scripts': [
            'zedenv=zedenv.main:cli'
        ],
    },
    zip_safe=False,
)