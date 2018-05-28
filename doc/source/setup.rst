..  index:: System Setup

System Setup
============

In order to use boot environments your system needs to be set up in a certain
manner. 

The main data set that is used for your root file system, can also be thought
of as your boot environment. Anything in this data set, or in a dataset under
it, is what constitutes a boot environment. 

Dataset Configuration 
--------------------- 

To put your system in a compatible configuration, your boot environments for
your system should be kept in a 'Boot Environment root'. In most configurations
this would be ``<pool>/ROOT``. However its location is not important, and it
can be located anywhere within a pool. What's important is that it does not
have any child data sets that are not in a boot environment.

The common practice is to start with a 'default' boot environment. This would
be the dataset ``<pool>/ROOT/default``. If a system is in this
manner, it would be the most basic boot environment compatible system.

This 'default' dataset could have the entire system installed into it. Upon
creating new boot environments it would be cloned and the entire system would
be in the new boot environment. A better practice would be to keep some
datasets separate from the boot environment, parts of the system that
would be shared between boot environments, would be located in these datasets.
For example, one might want to keep their logs separate, or their home
directories separate.

Examples
--------

Here are a few examples of possible setups with a few different systems.

FreeBSD
~~~~~~~

The default FreeBSD configuration is a great example of a hierarchy that is
setup to use boot environments by default. After a root on ZFS install, the
system has a new boot environment, that is usable by default.

Any data set that is set to ``canmount=off``, means it will not be mounted and
its data will be stored in the boot environment. 

In the default setup this means the data of ``/usr``, and ``/var`` will change
between boot environments, but any dataset set ``canmount=on``, will not be
in the boot environment, and the data will be persistent between every boot environment.

.. code-block:: none

    NAME                CANMOUNT  MOUNTPOINT
    zroot                     on  /zroot
    zroot/ROOT                on  none
    zroot/ROOT/default    noauto  /
    zroot/tmp                 on  /tmp
    zroot/usr                off  /usr
    zroot/usr/home            on  /usr/home
    zroot/usr/ports           on  /usr/ports
    zroot/usr/src             on  /usr/src
    zroot/var                off  /var
    zroot/var/audit           on  /var/audit
    zroot/var/crash           on  /var/crash
    zroot/var/log             on  /var/log
    zroot/var/mail            on  /var/mail
    zroot/var/tmp             on  /var/tmp

Arch Linux
~~~~~~~~~~

Here is an Arch Linux system, with an extensive dataset setup.

.. code-block:: none

    NAME                                          CANMOUNT  MOUNTPOINT
    vault/ROOT                                          on  none
    vault/ROOT/default-3                            noauto  /
    vault/ROOT/default-4                            noauto  /
    vault/home                                          on  legacy
    vault/usr                                          off  /usr
    vault/usr/local                                     on  legacy
    vault/var                                          off  /var
    vault/var/abs                                       on  legacy
    vault/var/cache                                     on  legacy
    vault/var/cache/pacman                              on  legacy
    vault/var/lib                                      off  /var/lib
    vault/var/lib/docker                                on  legacy
    vault/var/lib/libvirt                               on  legacy
    vault/var/lib/machines                              on  legacy
    vault/var/lib/systemd                              off  /var/lib/systemd
    vault/var/lib/systemd/coredump                      on  legacy
    vault/var/log                                       on  legacy
    vault/var/log/journal                               on  legacy

In this example, while it looks like ``/var``, ``/var/lib``
``/var/lib/systemd``, and ``/usr`` are outside of the boot environment, they
have actually been set to ``canmount=off`` meaning they're not mounted and
are only there to create the ZFS dataset structure. This will put their data in
the boot environment dataset. Their properties will be inherited by any child
datasets. 

This allows us to take any datasets we would like to share between boot
environments, and create them under these datasets in hierarchy that is clear
and easy to understand. It means the user's ``/home``, ``/usr/local`` and
``/var/log`` directories, among others, data will stay the same when switching
between boot environments.
