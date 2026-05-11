#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY "$0"
    exit
fi

cd "$(dirname "$(realpath "$0")")"
/usr/bin/python3 main.py