#!/bin/bash
set -e

# Install basic test deps - numpy already in env image, now ensure pytest
pip3 install --break-system-packages -q pytest==8.4.1 2>/dev/null || pip3 install -q pytest==8.4.1 || pip install -q pytest==8.4.1

mkdir -p /logs/verifier

# Run tests - use CTRF if available, otherwise plain pytest
if command -v uvx >/dev/null 2>&1; then
    uvx --with pytest==8.4.1 --with pytest-json-ctrf==0.3.5 pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
    status=$?
else
    pytest /tests/test_outputs.py -rA -v --tb=short | tee /logs/verifier/test.log
    status=${PIPESTATUS[0]}
    # create dummy ctrf
    echo '{"tests":[]}' > /logs/verifier/ctrf.json
fi

if [ $status -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
  echo "All tests passed"
else
  echo 0 > /logs/verifier/reward.txt
  echo "Tests failed"
fi

exit $status
