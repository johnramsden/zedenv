from setuptools import setup, find_packages

from zedenv import __version__

tests_require = [
    'coverage',
    'pytest',
    'pytest-runner',
    'pytest-cov',
    'pytest-pycodestyle',
    'tox'
]

dev_require = [
    'Sphinx'
]


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='zedenv',
    version=__version__,
    description='Utility to manage Boot Environments using ZFS',
    long_description=readme(),
    url='http://github.com/johnramsden/zedenv',
    author='John Ramsden',
    author_email='johnramsden@riseup.net',
    license='BSD-3-Clause',
    classifiers=[
        'Development Status :: 3 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='cli',
    packages=find_packages(exclude=["*tests*", "test_*"]),
    install_requires=[
        'click',
        'pyzfscmds @ git+https://github.com/johnramsden/pyzfscmds.git@v0.1.5-beta'
    ],
    setup_requires=['pytest-runner'],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
        'dev': dev_require,
    },
    entry_points="""
        [console_scripts]
        zedenv = zedenv.main:cli
        [zedenv.plugins]
        systemdboot = zedenv.plugins.systemdboot:SystemdBoot
        freebsdloader = zedenv.plugins.freebsdloader:FreeBSDLoader
    """,
    zip_safe=False,
)
