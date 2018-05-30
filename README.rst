======
zedenv
======

.. image:: https://travis-ci.com/johnramsden/zedenv.svg
    :target: https://travis-ci.com/johnramsden/zedenv

ZFS boot environment manager

Documentation for the project can be found at `readthedocs <zedenv.readthedocs.io>`_.

``zedenv`` is still experimental and should not be used on production systems.

Install
=======

``zedenv`` requires python 3.6+, `pyzfscmds <https://github.com/johnramsden/pyzfscmds>`_, and ZFS running as the root
filesystem.

The system should also be configured in the format:

.. code:: shell

    ${zpool}/${optional_datasets}/${boot_environment_root}/${root_dataset}

For example, ``zpool/ROOT/default`` or ``zpool/sys/hostname/ROOT/default``.

``zedenv`` can be installed a few ways:

* From the `setup.py <setup.py>`_ directly.
* From the `Makefile <packaging/Makefile>`_.
* From the `Arch AUR <https://aur.archlinux.org/packages/zedenv/>`_.

First, clone the git repos.

.. code-block:: shell

    git clone https://github.com/johnramsden/pyzfscmds
    git clone https://github.com/johnramsden/zedenv

Makefile and setup.py
---------------------

To install without poluting your system, you can also create a directory somewhere
and install in a ``venv``, otherwise install to the system.

Optionally, create a ``venv`` and activate.

.. code-block:: shell

    python3.6 -m venv venv
    . venv/bin/activate

setup.py
~~~~~~~~

Enter the repos and install.

.. code-block:: shell

    cd pyzfscmds
    python setup.py install

    cd ../zedenv
    python setup.py install

Makefile
~~~~~~~~

Enter the ``packaging`` directory in the repos run ``make``, ``pyzfscmds`` must
be installed first.

.. code-block:: shell

    cd pyzfscmds/packaging
    make

    cd ../../zedenv/packaging
    make


How To Use
----------


``zedenv`` can be used to manage boot environments using ZFS. If your system
is set up in a way compatible with boot environments, you can start using
them right away.

Create and activate a new Boot Environment.

.. code-block:: shell

    $ zedenv create default-0
    $ zedenv activate default-0

This will make it the Boot Environment used on reboot.

.. code-block:: shell

    $ zedenv list

.. code-block:: none

    Name       Active   Mountpoint   Creation
    default    N        -            Wed-May-23-23:48-2018
    default-0  R        /            Thu-May-24-23:54-2018

This can be shown with a list, command. The boot environment currently being used will
have a 'N' in the active column signifying the boot environment is being used now.
An 'R' in the active column means this environment will be used on reboot.
