#!/usr/bin/env bash

set -e

PYTHON=python3
PIP=pip3

sudo apt-get install libbluetooth-dev \
  libglib2.0-dev \
  libboost-python-dev \
  libboost-thread-dev \
  python-pip \
  python-bluez \
  libbluetooth-dev \
  libboost-python-dev \
  libboost-thread-dev \
  libglib2.0-dev bluez \
  bluez-hcidump


$PIP install --user gattlib \
  pybluez \
  scapy

$PYTHON -c 'import bluetooth' 2&> /dev/null
res=$?
if [[ $res = 0 ]]
then
  echo SkullPosDude Done. enjoy!
else
  echo The install failed, sorry.
fi
exit $res
