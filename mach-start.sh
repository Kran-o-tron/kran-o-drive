#!/usr/bin/env bash
if [ $0 == "-gui" ]; then
    if [ -z $1 ]; then
        echo "NO BLUETOOTH ADDRESS SUPPLIED"
        exit 0
    else
        echo "STARING WITH GUI"
        python3 mach.py -gui $1 2>&1 | head -n 1
    fi
else
    if [ -z $0 ]; then
        echo "NO BLUETOOTH ADDRESS SUPPLIED"
    else
        echo "STARING WITHOUT GUI"
        python3 mach.py $0
    fi
fi

