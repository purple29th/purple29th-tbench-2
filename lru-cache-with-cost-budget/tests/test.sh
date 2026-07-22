#!/bin/bash
set +e
mkdir -p /logs/verifier

# Anti-cheat hardening: hide /tests during agent binary execution so agent cannot import CASES
# CASES now holds only digests not plaintext, but hide anyway for depth defense
if [ -d /tests ]; then mv /tests /tmp/tests.hidden; fi
# run agent binary for each hardcoded input? Actually test file does subprocess calls, not this script
# So we just ensure binary exists and can run; hide does not affect pytest subprocess if restored before pytest
if [ -d /tmp/tests.hidden ]; then mv /tmp/tests.hidden /tests; fi

# As extra defense, clear any stale output and fail closed if binary not built would be handled in test file
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
