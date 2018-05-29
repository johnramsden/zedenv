..  index:: Install

Install
=======

``zedenv`` requires python 3.6+, `pyzfscmds <https://github.com/johnramsden/pyzfscmds>`_, and ZFS running as the root
filesystem.

It can be installed a few ways:

* From the ``setup.py`` directly.
* From the ``Makefile``.
* From the arch ``PKGBUILD``

First, clone the git repos.

.. code-block:: shell

    git clone https://github.com/johnramsden/pyzfscmds
    git clone https://github.com/johnramsden/zedenv

Arch
----

Install ``pyzfscmds`` and ``zedenv`` by entering ``packaging/arch`` and running ``makepkg -sic``.

.. code-block:: shell

    cd pyzfscmds/packaging/arch
    makepkg -sic

    cd ../../zedenv/packaging/arch
    makepkg -sic

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

    cd ../zedenv pyzfscmds
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
