#!/usr/bin/env bash
set -e
sudo hciconfig hci0 piscan
sudo python3 rasp.py 0