#!/bin/bash
set +e
mkdir -p /verifier
pip install --quiet --disable-pip-version-check pytest==8.3.3 > /dev/null 2>&1
python3 -m pytest /tests/test_outputs.py -rA --tb=short > /verifier/test-stdout.txt 2>&1
status=$?
if [ $status -eq 0 ]; then
        echo 1 > /verifier/reward.txt
else
        echo 0 > /verifier/reward.txt
fi
exit 0
