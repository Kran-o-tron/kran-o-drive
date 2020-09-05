#!/bin/bash
# $1 - bluetooth_addr
# $2 -> $... flags
#set -e

# remove any current SkullBot processes
#ps ax

ps ax | grep mach.py | grep -v grep | awk '{print $1}' | xargs kill
ps ax | grep gui.py | grep -v grep | awk '{print $1}' | xargs kill

#pkill *mach.py*


echo "${@}"
python3 gui.py 55555 &
#pid_gui=$!

python3 mach.py -gui "${@}"
#pid_mach=$!
