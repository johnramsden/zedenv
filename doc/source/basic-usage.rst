..  index:: Basic Usage

Basic Usage
===========

``zedenv`` can be used to manage boot environments using ZFS. If your system
is set up in a way compatible with boot environments, you can start using
them right away.

Create and activate a new Boot Environment. 

.. code-block:: shell

    zedenv create default-0
    zedenv activate default-0

This will make it the Boot Environment used on reboot.

.. code-block:: none

    Name       Active   Mountpoint   Creation              
    default    N        -            Wed-May-23-23:48-2018 
    default-0  R        /            Thu-May-24-23:54-2018

This can be shown with a list, command. The boot environment currently being used will
have a 'N' in the active column signifying the boot environment is being used now.
An 'R' in the active column means this environment will be used on reboot

In order for reboot to work successfully with a bootloader, an extra flag
'``-b/--bootloader``' must be used to specify a bootloader plugin. The plugin will make the necessary changes
to boot from the new Boot Environment. 

Plugins available for your system can be listed with ``zedenv --plugins``. 

If you're using ``zedenv`` to activate a boot environment, and a plugin isn't available, you
will probably need to edit some config files to specify the new dataset, depending on
your bootloader.

Usage information can be given at any time by running ``zedenv --help``. 

.. code-block:: none

    Usage: zedenv [OPTIONS] COMMAND [ARGS]...

    ZFS boot environment manager cli

    Options:
    --version
    --plugins  List available plugins.
    --help     Show this message and exit.

    Commands:
    activate  Activate a boot environment.
    create    Create a boot environment.
    destroy   Destroy a boot environment or snapshot.
    list      List all boot environments.
    mount     Mount a boot environment temporarily.
    rename    Rename a boot environment.
    umount    Unmount a boot environment.

More specific information about a specific subcommand can be requested as well.

.. code-block:: shell

    zedenv create --help

.. code-block:: none

    Usage: zedenv create [OPTIONS] BOOT_ENVIRONMENT

    Create a boot environment.

    Options:
    -v, --verbose        Print verbose output.
    -e, --existing TEXT  Use existing boot environment as source.
    --help               Show this message and exit.

