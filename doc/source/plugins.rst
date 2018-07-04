..  index:: Plugins

Plugins
========

As of now plugins for the following bootloaders exist:

* FreeBSD's loader - ``freebsdloader``
* systemdboot - ``systemdboot``

In order to integrate with a bootloader, an extra flag '``-b/--bootloader``'
must be used to specify a bootloader plugin. The plugin will make the necessary
changes to boot from the new Boot Environment.

If you expect you will always be using a certain bootloader, you can set the
``org.zedenv:bootloader`` property on your boot environments, and the
bootloader plugin will be used without you having to specify. 

.. code-block:: shell

    $ zedenv set org.zedenv:bootloader=<bootloader plugin>

Plugins available for your system can be listed with ``zedenv --plugins``. 

freebsdloader
-------------

The ``freebsdloader`` plugin is quite simple. During activation, it will
respect ``/etc/rc.d/zfsbe`` if it exists, and set, all datasets to
``canmount=noauto``, otherwise the datasets will be set ``canmount=on``. 

It will also change the root dataset to mount from in ``/boot/loader.conf``,
and ``/boot/loader.conf.local``. 

The current ``/boot/zfs/zpool.cache`` will also be copied into the newly
activated boot environment.

systemdboot
-----------

Multiple kernels can be managed with this plugin and systemd-boot, but it will
require changing the mountpoint of the esp (EFI System Partition).

Problem With Regular Mountpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Usually the ``$esp`` would get mounted at ``/boot`` or ``/boot/efi``. The
kernels would sit in the root of the ``$esp``, and the configs for systemdboot
in ``$esp/loader/``.

.. code-block:: none

    $esp 
    . 
    ├── initramfs-linux-fallback.img 
    ├── initramfs-linux.img 
    ├── intel-ucode.img 
    ├── vmlinuz-linux 
    │ 
    └── loader/ 
        ├── entries/ 
        │   └── arch.conf 
        └── loader.conf 

The configs would then reference kernels in the root directory.

.. code-block:: none

    title           Arch Linux 
    linux           vmlinuz-linux 
    initrd          intel-ucode.img 
    initrd          initramfs-linux.img 
    options         zfs=bootfs rw 

The problem with this method, is multiple kernels cannot be kept at the same
time. Therefore this hierarchy is not conducive to boot environments.


Alternate Mountpoint
~~~~~~~~~~~~~~~~~~~~

First, remount the ``$esp`` to a new location, the default is ``/mnt/efi``.

If you would like to explicitly specify the mountpoint used, you can set the
``org.zedenv.systemdboot:esp`` property on your current boot environment, and the plugin
will use the specified location: 

.. code-block:: shell

    zfs set org.zedenv.systemdboot:esp='/mnt/efi' zpool/ROOT/default

Don't forget to change the mount point in ``/etc/fstab``.

.. code-block:: none

    UUID=9F8A-F566            /mnt/efi  vfat    rw,defaults,errors=remount-ro  0 2

Now, make a subdirectory ``$esp/env``, kernels will be kept in a subdirectory
of this location.

The bootloader configuration can now use a different path for each boot
environment.

So the 'default' boot environment config, located at
``$esp/loader/entries/zedenv-default.conf``, would look something like:

.. code-block:: none

    title           Arch Linux
    linux           /env/zedenv-default/vmlinuz-linux
    initrd          /env/zedenv-default/intel-ucode.img
    initrd          /env/zedenv-default/initramfs-linux.img
    options         zfs=zpool/ROOT/default rw

To make the system happy when it looks for kernels at ``/boot``, this directory
should be bindmounted to ``/boot``. 

Bindmount ``/mnt/efi/env/zedenv-default`` to ``/boot`` in ``/etc/fstab``.

.. code-block:: none

    /mnt/efi/env/zedenv-default   /boot     none    rw,defaults,errors=remount-ro,bind    0 0

If this directory is not here, the kernels will not be updated when the system
rebuilds the kernel.

Once our system is set up in the proper configuration, ``zedenv`` will update
the bootloader, and fstab - if requested - when a new boot environment is
activated.

It will also update the configuration described above, asking you if the
modifications that made are correct. You will have a chance to inspect and
change them if they are not. 

If you are confident and the changes it is making, and do not wish to inspect
them, adding the ``--noconfirm/-y`` flag will run the command without asking
for confirmation.

