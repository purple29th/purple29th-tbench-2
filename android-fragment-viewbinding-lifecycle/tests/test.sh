#!/bin/bash
set +e
rm -rf /app/build
mkdir -p /logs/verifier

if command -v uvx >/dev/null 2>&1; then
  uvx --python 3.12 --with pytest==8.3.3 \
          pytest /tests/test_outputs.py -rA --tb=short \
          > /logs/verifier/test-stdout.txt 2>&1
  status=$?
else
  python3 -m pytest /tests/test_outputs.py -rA --tb=short \
          > /logs/verifier/test-stdout.txt 2>&1
  status=$?
  if [ $status -ne 0 ]; then
    python -m pytest /tests/test_outputs.py -rA --tb=short \
            > /logs/verifier/test-stdout.txt 2>&1
    status=$?
  fi
fi

if [ $status -eq 0 ]; then
        echo 1 > /logs/verifier/reward.txt
else
        echo 0 > /logs/verifier/reward.txt
fi
exit 0
