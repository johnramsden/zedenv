..  index:: Commands

Commands
========

The following commands are available

* ``activate`` - Activate a boot environment.
* ``create`` - Create a boot environment.
* ``destroy`` - Destroy a boot environment or snapshot.
* ``list`` - List all boot environments.
* ``mount`` - Mount a boot environment temporarily.
* ``rename`` - Rename a boot environment.
* ``umount`` - Unmount a boot environment.

Activate
--------

The ``activate`` is used to enable an already created boot environment. After
activation, the boot environment will be used upon reboot.

.. code-block:: shell

    zedenv activate [OPTIONS] BOOT_ENVIRONMENT


.. table::

    ===================================  =========================================================
     Option                                Description
    ===================================  =========================================================
     ``-v``, ``--verbose``                 Print verbose output.
     ``-b``, ``--bootloader`` ``TEXT``     Use bootloader type.
     ``-y``, ``--noconfirm``               Assume yes in situations where confirmation is needed.
     ``-n``, ``--noop``                    Print what would be destroyed but don't apply.
     ``--help``                            Show this message and exit.
    ===================================  =========================================================

Create
------

Create a new boot environment.

.. code-block:: shell

    zedenv create [OPTIONS] BOOT_ENVIRONMENT

.. table::

    ===================================  =========================================================
     Option                                Description
    ===================================  =========================================================
     ``-v``, ``--verbose``                 Print verbose output.
     ``-e``, ``--existing`` ``TEXT``       Use existing boot environment as source.
     ``--help``                            Show this message and exit.
    ===================================  =========================================================

Destroy
-------

Destroy a boot environment or snapshot.

.. code-block:: shell

    zedenv destroy [OPTIONS] BOOT_ENVIRONMENT

.. table::

    ===================================  =========================================================
     Option                                Description
    ===================================  =========================================================
     ``-v``, ``--verbose``                 Print verbose output.
     ``-b``, ``--bootloader`` ``TEXT``     Use bootloader type.
     ``-y``, ``--noconfirm``               Assume yes in situations where confirmation is needed.
     ``-n``, ``--noop``                    Print what would be destroyed but don't apply.
     ``--help``                            Show this message and exit.
    ===================================  =========================================================

List
----

List all boot environments.

.. code-block:: shell

    zedenv list [OPTIONS]


.. table::

    ===================================  =========================================================
     Option                                Description
    ===================================  =========================================================
     ``-v``, ``--verbose``                 Print verbose output.
     ``-D``, ``--spaceused``               Display the full space usage for each boot environment.
     ``-H``, ``--scripting``               Scripting output.
     ``-O``, ``--origin``                  Display origin.
     ``--help``                            Show this message and exit.
    ===================================  =========================================================


Mount
-----

Mount a boot environment temporarily.

.. code-block:: shell

     zedenv mount [OPTIONS] BOOT_ENVIRONMENT [MOUNTPOINT]

.. table::

    ===================================  =========================================================
     Option                                Description
    ===================================  =========================================================
     ``-v``, ``--verbose``                 Print verbose output.
     ``--help``                            Show this message and exit.
    ===================================  =========================================================

Rename
------

Rename a boot environment.

.. code-block:: shell


    zedenv rename [OPTIONS] BOOT_ENVIRONMENT NEW_BOOT_ENVIRONMENT

.. table::

    ===================================  =========================================================
     Option                                Description
    ===================================  =========================================================
     ``-v``, ``--verbose``                 Print verbose output.
     ``--help``                            Show this message and exit.
    ===================================  =========================================================




Umount
------

Unmount a boot environment.

.. code-block:: shell

    zedenv umount [OPTIONS] BOOT_ENVIRONMENT

.. table::

    ===================================  =========================================================
     Option                                Description
    ===================================  =========================================================
     ``-v``, ``--verbose``                 Print verbose output.
     ``--help``                            Show this message and exit.
    ===================================  =========================================================


