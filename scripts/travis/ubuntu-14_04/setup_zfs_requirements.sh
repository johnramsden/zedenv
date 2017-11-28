#!/bin/sh

# Travis setup script

# Install zfs requirements
add-apt-repository -y ppa:zfs-native/stable && \
apt-get -q update && \
apt-get install -y linux-headers-$(uname -r) && \
apt-get install -y ubuntu-zfs || exit 1


