zedenv
======

.. image:: https://travis-ci.com/johnramsden/zedenv.svg?token=4X1vWwTyHTHCUwBTudyN&branch=release/v0.0.2
    :target: https://travis-ci.com/johnramsden/zedenv

ZFS boot environment manager

Requirements
------------

``zedenv`` requires python 3.6+, and ZFS running as the root filesystem.

The system should also be configured in the format:

.. code:: shell

    ${zpool}/${optional_datasets}/${boot_environment_root}/${root_dataset}

For example, ``zpool/ROOT/default`` or ``zpool/sys/hostname/ROOT/default``.

Installing
---------

``zedenv`` can be installed by cloning the repo, and running the ``setup.py`` script.

.. code:: shell

    $ git clone https://github.com/johnramsden/zedenv
    $ cd zedenv
    $ python setup.py install

Quick How-to
------------

To check the options run ``zedenv --help``.

Create a new boot environment

.. code:: shell

    $ zedenv create -v zedenv-$(date +%Y-%m-%d-%H%M%S)

List boot environments

.. code:: shell

    $ zedenv list
    default
    zedenv-2017-11-21-231400

Testing
-------

To test using pytest, run it from the tests directory with a zfs dataset.

.. code:: shell

    $ pytest --root-dataset="zpool/ROOT/default"

To test coverage run pytest wuth the pytest-cov plugin.

.. code:: shell

    $ pytest --root-dataset="zpool/ROOT/default" --cov=zedenv
