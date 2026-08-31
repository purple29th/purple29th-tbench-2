#!/bin/bash
set -euo pipefail
mkdir -p /tmp
rm -rf /app/conftest.py 2>/dev/null || true
rm -rf /tmp/test-stdout.txt /tmp/test-stderr.txt
rm -rf /logs/verifier 2>/dev/null || true
mkdir -p /logs/verifier 2>/dev/null || true
mkdir -p /tmp/web_oracle/logs/verifier 2>/dev/null || true
cd /app 2>/dev/null || cd /tmp/web_oracle/app 2>/dev/null || true
python3 -m pytest tests/test_outputs.py -v 2>&1 | tee /tmp/test-stdout.txt
pytest_status=${PIPESTATUS[0]}
if [ $pytest_status -eq 0 ]; then
  mkdir -p /logs/verifier
  echo 1 > /logs/verifier/reward.txt
  mkdir -p /tmp/web_oracle/logs/verifier
  echo 1 > /tmp/web_oracle/logs/verifier/reward.txt
else
  mkdir -p /logs/verifier
  echo 0 > /logs/verifier/reward.txt
  mkdir -p /tmp/web_oracle/logs/verifier
  echo 0 > /tmp/web_oracle/logs/verifier/reward.txt
fi
exit $pytest_status
