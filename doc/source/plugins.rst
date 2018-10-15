..  index:: Plugins

Plugins
========

As of now plugins for the following bootloaders exist:

* FreeBSD's loader - ``freebsdloader``
* systemd-boot - ``systemdboot``
* GRUB (alpha) - ``grub``

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

    zedenv set org.zedenv.systemdboot:esp='/mnt/efi'

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

GRUB
----

GRUB support is provided via `external plugin <https://github.com/johnramsden/zedenv-grub/>`_. 

One of two types of setup can be used with grub.

* Boot on ZFS - separate ``grub`` dataset needed.
* Separate partition for kernels

Boot on ZFS (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~

To use boot on ZFS:

* A ``grub`` dataset is needed. It should be mounted at ``/boot/grub``.
* ``org.zedenv.grub:bootonzfs`` should be set to ``yes``
* Individual boot environments should contain their kernels in ``/boot``, which should be part of the root dataset.

To convert an existing grub install, set up the ``grub`` dataset, and mount it. Then install grub again. 

.. code-block:: shell

    zfs create -o canmount=off zroot/boot
    zfs create -o mountpoint=legacy zroot/boot/grub
    mount -t zfs zroot/boot/grub /boot/grub

    # efi
    mount ${esp} /boot/efi
    grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB

    # or for BIOS
    grub-install --target=i386-pc /dev/sdx --recheck

If you get:

.. code-block:: shell

    /dev/sda
    Installing for i386-pc platform.
    grub-install: error: failed to get canonical path of `/dev/ata-SAMSUNG_SSD_830_Series_S0VVNEAC702110-part2'.

A workaround is to symlink the expected partition to the id

.. code-block:: shell
    
    ln -s /dev/sda2 /dev/ata-SAMSUNG_SSD_830_Series_S0VVNEAC702110-part2

Separate Partition for Kernels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An example system on Arch Linux with a separate partition for kernels would be the following:

* Boot partition mounted to ``/mnt/boot``. 
* The directory containing kernels for the active boot environment, ``/mnt/boot/env/zedenv-${boot_env}`` bind mounted to ``/boot``. 
* The grub directory ``/mnt/boot/grub`` bindmounted to ``/boot/grub``
* ``org.zedenv.grub:bootonzfs`` should be set to ``no``

What this would look like during an arch Linux install would be the following: 

.. code-block:: shell

    zpool import -d /dev/disk/by-id -R /mnt vault

    mkdir -p /mnt/mnt/boot /mnt/boot
    mount /dev/sda1 /mnt/mnt/boot

    mkdir /mnt/mnt/boot/env/zedenv-default /mnt/boot/grub
    mount --bind /mnt/mnt/boot/env/zedenv-default /mnt/boot
    mount --bind /mnt/mnt/boot/grub /mnt/boot/grub

    genfstab -U -p /mnt >> /mnt/etc/fstab

    arch-chroot /mnt /bin/bash

In chroot

.. code-block:: shell

    export ZPOOL_VDEV_NAME_PATH=1

    grub-install --target=x86_64-efi --efi-directory=/mnt/boot --bootloader-id=GRUB
    grub-mkconfig -o /boot/grub/grub.cfg

Converting Existing System
~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a backup. 

.. code-block:: shell

    cp /boot /boot.bak

Unmount ``/boot``, and remount it at ``/mnt/boot``.

.. code-block:: shell

    mkdir -p /mnt/boot
    mount /dev/sdxY /mnt/boot

Then you want to move your current kernel to ``/mnt/boot/env/zedenv-${boot_env_name}``

.. code-block:: shell

    mkdir /mnt/boot/env/zedenv-default
    mv /mnt/boot/* /mnt/boot/env/zedenv-default 

Move the grub directory back if it was also moved (or don't move it in the first place).

.. code-block:: shell

    mv /mnt/boot/env/zedenv-default/grub /mnt/boot/grub

Now bindmount the current kernel directory to ``/boot`` so that everything is where the system expects it.

.. code-block:: shell

    mount --bind /mnt/boot/env/zedenv-default /boot

Same thing with the grub directory 

.. code-block:: shell

    mount --bind /mnt/boot/grub /boot/grub 

Now everything is back to appearing how it looked originally, but things are actually stored in a different place. 

You're also probably going to want to update your fstab, if you're using Arch you can use genfstab, which requires ``arch-install-scripts``. 

.. code-block:: shell

    genfstab -U -p / 

You'll need to add the output to ``/etc/fstab.`` 

This is what an example looks like.

.. code-block:: shell

    # /dev/sda1
    UUID=B11F-0328          /mnt/boot       vfat            rw,relatime,fmask=0022,dmask=0022,codepage=437,iocharset=iso8859-1,shortname=mixed,utf8,errors=remount-ro       0 2

    /mnt/boot/env/zedenv-grub-test-3        /boot           none            rw,fmask=0022,dmask=0022,codepage=437,iocharset=iso8859-1,shortname=mixed,utf8,errors=remount-ro,bind   0 0
    /mnt/boot/grub          /boot/grub      none            rw,fmask=0022,dmask=0022,codepage=437,iocharset=iso8859-1,shortname=mixed,utf8,errors=remount-ro,bind   0 0 


Post Setup
~~~~~~~~~~

After install, run ``zedenv --plugins``, you should see ``grub``.
 
``zedenv`` will do its best to decide whether or not you are booting off of an all ZFS system, but it can also be set explicitly with ``org.zedenv.grub:bootonzfs=yes``.

Any values you have set explicitly will show up with ``zedenv get``.

You may want to disable all of the grub generators in ``/etc/grub.d/`` except for ``00_header`` and the zedenv generator ``05_zfs_linux.py`` by removing the executable bit.

