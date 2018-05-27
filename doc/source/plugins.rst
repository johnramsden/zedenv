..  index:: Plugins

Plugins
========

As of now there are two bootloader plugins, the one for FreeBSD's loader, and one for systemdboot.

systemdboot
-----------

Multiple kernels can be managed with this plugin and systemd-boot, but it will
require changing the mountpoint of the esp (EFI System Partition).

Problem With Regular Mountpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Usually the ``$esp`` would get mounted at ``/boot`` or ``/boot/efi``. The kernels
would sit in the root of the ``$esp``, and the configs for systemdboot in
``$esp/loader/``.

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
        │   └── arch.conf
        └── loader.conf

The configs would then reference kernels in the root directory.

.. code-block:: none

    title           Arch Linux
    linux           vmlinuz-linux
    initrd          intel-ucode.img
    initrd          initramfs-linux.img
    options         zfs=bootfs rw

The problem with this method, is multiple kernels cannot be kept at the same time.
Therefore this hierarchy is not conducive to boot environments.


Alternate Mountpoint
~~~~~~~~~~~~~~~~~~~~

First, remount the ``$esp`` to a new location, I use ``/mnt/efi`` in my ``/etc/fstab``:

.. code-block:: none

    UUID=9F8A-F566            /mnt/efi  vfat  rw,relatime,fmask=0022,dmask=0022,codepage=437,iocharset=iso8859-1,shortname=mixed,errors=remount-ro      0 2

Now, make a subdirectory ``$esp/env``, kernels will be kept in a subdirectory of this location.

The bootloader configuration can now use a different path for each boot environment.

So the 'default' boot environment would look like:

.. code-block:: none

    title           Arch Linux
    linux           /env/default/vmlinuz-linux
    initrd          /env/default/intel-ucode.img
    initrd          /env/default/initramfs-linux.img
    options         zfs=bootfs rw

To make the system happy when it looks for kernels in the default location, this directory can be
bindmounted to ``/boot``. To do so add the following to ``/etc/fstab``.

    /mnt/efi/env/default   /boot     none  rw,relatime,fmask=0022,dmask=0022,codepage=437,iocharset=iso8859-1,shortname=mixed,errors=remount-ro,bind 0 0

If this directory is not here, the kernels will not be updated when the system rebuilds the kernel.

Once our system is set up in the proper configuration, ``zedenv`` will update your bootloader and
fstab - if requested - when a new boot environment is created.



