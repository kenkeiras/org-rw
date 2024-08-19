#!/bin/sh

set -eu

cd "`dirname $0`"
cd ..

set -x

isort --profile black .
black .
