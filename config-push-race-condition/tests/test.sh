#!/bin/bash
set +e
mkdir -p /logs/verifier

cd /app
rm -f /app/output.txt
# Hide /tests during agent code execution so agent cannot read expected.txt at grade time
if [ -d /tests ]; then mv /tests /tmp/tests.hidden; fi
kotlinc src/com/example/cfgpush/*.kt -include-runtime -d /app/sim.jar \
    >> /logs/verifier/build.log 2>&1
build_status=$?

if [ $build_status -ne 0 ]; then
    echo "build failed (status $build_status) — failing closed" >> /logs/verifier/build.log
    echo 0 > /logs/verifier/reward.txt
    if [ -d /tmp/tests.hidden ]; then mv /tmp/tests.hidden /tests; fi
    exit 0
fi

java -jar /app/sim.jar >> /logs/verifier/run.log 2>&1

cp /app/output.txt /logs/verifier/output.txt 2>/dev/null || true

# Restore tests before pytest
if [ -d /tmp/tests.hidden ]; then mv /tmp/tests.hidden /tests; fi

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
