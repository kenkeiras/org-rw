#!/bin/sh

set -eu

cd "`dirname $0`"
cd ..

pandoc README.org -o README.md  # PyPI doesn't accept Org files

python setup.py sdist

twine upload --verbose dist/*
