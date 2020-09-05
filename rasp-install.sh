#!/usr/bin/env bash

set -e

PYTHON=python3
PIP=pip3

adduser lp $(whoami)

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
  bluez-hcidump \
  python-smbus \
  i2c-tools

sudo python3 -m pip install --user gattlib \
  pybluez \
  adafruit-circuitpython-motorkit


$PYTHON -c 'import bluetooth' 2&> /dev/null
res=$?
if [[ $res = 0 ]]
then
  echo SkullBot setup done, enjoy!
else
  echo The install failed, sorry.
fi
exit $res
