#!/bin/bash

# remove any current SkullBot processes

ps ax | grep mach.py | grep -v grep | awk '{print $1}' | xargs kill
ps ax | grep gui.py | grep -v grep | awk '{print $1}' | xargs kill

echo "${@}"
python3 gui.py 55555 &
#pid_gui=$!

python3 mach.py -gui "${@}"
#pid_mach=$!
