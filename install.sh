#!/usr/bin/env bash

set -e

PYTHON=python3
PIP=pip3

sudo apt-get install libbluetooth-dev \
  libglib2.0-dev \
  libboost-python-dev \
  libboost-thread-dev

$PIP install --user gattlib \
  pybluez

$PYTHON -c 'import bluetooth' 2&> /dev/null
res=$?
if [[ $res = 0 ]]
then
  echo Done.
else
  echo The install failed, sorry.
fi
exit $res
