#!/bin/sh

set -eu

# Get to the script's directory
cd "`dirname $0`"

# Update the extra submodules
git submodule update --init --recursive .

# Run all checks
python3 org_dom_check.py .
