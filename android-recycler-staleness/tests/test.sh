#!/bin/bash
set +e
mkdir -p /logs/verifier

uvx --python 3.12 --with pytest==8.3.3 \
        pytest /tests/test_outputs.py -rA --tb=short \
        > /logs/verifier/test-stdout.txt 2>&1
status=$?

if [ $status -eq 0 ]; then
        echo 1 > /logs/verifier/reward.txt
else
        echo 0 > /logs/verifier/reward.txt
fi
exit 0
