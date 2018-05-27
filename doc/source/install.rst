..  index:: Install zedenv

Install
=======

``zedenv`` can be installed a faw ways:

* In a ``venv``
* From the arch ``PKGBUILD``

To start, clone the git repos.

.. code-block:: shell

    git clone https://github.com/johnramsden/pyzfscmds
    git clone https://github.com/johnramsden/zedenv

Arch
----

Install ``pyzfscmds`` and ``zedenv`` by entering ``packaging/arch`` and running ``makepkg -sic``.

Virtualenv
----------

To install without poluting your system, you can also create a directory somewhere
and install in a ``venv``.

Create ``venv`` and activate.

.. code-block:: shell

    python3.6 -m venv venv
    . venv/bin/activate

Enter the repos and install.

.. code-block:: shell

    cd pyzfscmds
    python setup.py install

    cd ../zedenv pyzfscmds
    python setup.py install
