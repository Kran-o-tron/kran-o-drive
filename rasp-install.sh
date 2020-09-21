#!/usr/bin/env bash

set -e

PYTHON=python3
PIP=pip3

adduser lp $(whoami)

sudo apt-get install python-smbus \
  i2c-tools

sudo python3 -m pip install --user gattlib \
  adafruit-circuitpython-motorkit

echo SkullBot setup done, enjoy!