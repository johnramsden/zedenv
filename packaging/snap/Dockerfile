FROM ubuntu:18.04
MAINTAINER John Ramsden <johnramsden@riseup.net>

ENV LC_ALL C.UTF-8
ENV SNAPCRAFT_SETUP_CORE 1

ENV BUILD_USER builder
ENV BUILD_HOME /home/"${BUILD_USER}"
ENV BUILD_DIR "${BUILD_HOME}"/zedenv
ARG USER_ID=1000

RUN apt-get update && \
    apt-get dist-upgrade --yes && \
    apt-get install --yes \
            sudo build-essential snapcraft \
            python3-all python3-dev python3-pip && \
    apt-get autoremove --yes && apt-get clean --yes

RUN echo '%sudo ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
RUN mkdir -p "${BUILD_HOME}"
RUN useradd -u "${USER_ID}" -s /bin/bash -d "${BUILD_HOME}"  -G sudo "${BUILD_USER}"
RUN chmod -R 777 "${BUILD_HOME}"
RUN chown -R $BUILD_USER "${BUILD_HOME}"

VOLUME $BUILD_DIR
WORKDIR $BUILD_DIR
USER $BUILD_USER
