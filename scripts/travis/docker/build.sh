#!/bin/sh

PACKAGE_DIR="$(pwd)/packaging/snap"
BUILD_USER="builder"
DOCKER_TAG="python-snap"

docker build -f ${PACKAGE_DIR}/Dockerfile \
             --build-arg USER_ID="$(id -u)" \
             --tag="${DOCKER_TAG}" .

docker run --rm --volume=${PACKAGE_DIR}:/home/"${BUILD_USER}"/zedenv \
        "${DOCKER_TAG}" sudo sh -c 'snapcraft && snapcraft clean'
