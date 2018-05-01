from setuptools import setup, find_packages

from zedenv import __version__

tests_require = [
    'coverage',
    'pytest',
    'pytest-runner',
    'pytest-cov',
    'pytest-pep8',
    'tox'
]

dev_require = [
    'Sphinx'
]

dependency_links = [
     'git+ssh://git@github.com/johnramsden/pyzfsutils.git#egg=pyzfsutils'
]


def readme():
    with open('README.rst') as f:
        return f.read()

# Install all with:
# pip install -e .
# pip install '.[dev]' '.[test]' \
# --process-dependency-links git+ssh://git@github.com/johnramsden/pyzfsutils.git#egg=pyzfsutils
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
    packages=find_packages(),
    install_requires=['click', 'pyzfsutils'],
    setup_requires=['pytest-runner'],
    dependency_links=dependency_links,
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
    """,
    zip_safe=False,
)
