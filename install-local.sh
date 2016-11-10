#!/usr/bin/env bash
if command -v pip3 >/dev/null 2>&1; then
    pip3 install --user -e .
elif command -v pip >/dev/null 2>&1; then
    pip install --user -e .
else
    echo "Could not find a copy of python pip on this system. Aborting"
fi