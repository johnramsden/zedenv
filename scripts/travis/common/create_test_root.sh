#!/bin/sh

# Defaults if none give on cli
TEST_POOL="${1:-zpool}"
TEST_DATASET="${2:-${TEST_POOL}/ROOT/default}"

ZEDENV_DIR="${PWD}/zfstests"
TEST_DISK="${ZEDENV_DIR}/disk.img"

ZPOOL_ROOT_MOUNTPOINT="${ZEDENV_DIR}/root"

modprobe zfs || exit 1

mkdir -p ${ZEDENV_DIR} || exit 1

truncate -s 100M "${TEST_DISK}" && zpool create "${TEST_POOL}" "${TEST_DISK}"
if [ $? -ne 0 ]; then
    echo "Failed to create test pool ""'""${TEST_POOL}""'"" with disk ""'""${TEST_DISK}"
    exit 1
fi

mkdir -p "${ZPOOL_ROOT_MOUNTPOINT}" && \
zfs create -p -o mountpoint="${ZPOOL_ROOT_MOUNTPOINT}" "${TEST_DATASET}"
if [ $? -ne 0 ]; then
    echo "Failed to create test dataset ""'""${TEST_DATASET}""'"
    exit 1
fi

# Allow user usage of zfs
chmod u+s "$(which zfs)" "$(which zpool)" "$(which mount)" || exit 1
