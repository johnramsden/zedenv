#!/bin/sh

# Travis setup script (16.04

# Install zfs requirements
systemctl mask zfs-import-cache zfs-share zfs-mount
add-apt-repository -y ppa:jonathonf/zfs && \
apt-get -q update && \
apt-get install -y linux-headers-$(uname -r) && \
apt-get install -y spl-dkms zfs-dkms zfsutils-linux || exit 1
