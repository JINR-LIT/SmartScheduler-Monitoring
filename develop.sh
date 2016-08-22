#!/bin/bash
set -ev
deactivate || true
virtualenv -p python2.7 env
set +v
. env/bin/activate
set -v
pip install -r ./requirements.txt
pip install -e .
set +ev
