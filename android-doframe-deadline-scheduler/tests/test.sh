#!/bin/bash
set +e
mkdir -p /logs/verifier

# Anti-cheat hardening: hide /tests and scenario path derivation
# The agent's jar runs in the same filesystem at grade time, so expected files would be readable.
# Move them out of reach during agent execution and restore only for pytest.
if [ -d /tests ]; then mv /tests /tmp/tests.hidden; fi
if [ -d /app/scenarios ]; then mv /app/scenarios /tmp/scenarios.hidden; fi
mkdir -p /app/scenarios
cp -a /tmp/scenarios.hidden/*.txt /app/scenarios/ 2>/dev/null || true

cd /app
rm -f /app/output.*.txt
kotlinc src/com/example/choreographer/*.kt -include-runtime -d /app/sim.jar \
    >> /logs/verifier/build.log 2>&1
build_status=$?

if [ $build_status -ne 0 ]; then
    echo "build failed (status $build_status) — failing closed" >> /logs/verifier/build.log
    echo 0 > /logs/verifier/reward.txt
    # restore for completeness
    rm -rf /app/scenarios
    if [ -d /tmp/scenarios.hidden ]; then mv /tmp/scenarios.hidden /app/scenarios; fi
    if [ -d /tmp/tests.hidden ]; then mv /tmp/tests.hidden /tests; fi
    exit 0
fi

for scenario_file in /app/scenarios/*.txt; do
    name=$(basename "$scenario_file" .txt)
    java -jar /app/sim.jar "$scenario_file" "/app/output.${name}.txt" \
        >> /logs/verifier/run.log 2>&1
done

cp /app/output.*.txt /logs/verifier/ 2>/dev/null || true

# Restore tests and use a randomized mapping so output filename does not leak expected filename
rm -rf /app/scenarios
if [ -d /tmp/scenarios.hidden ]; then mv /tmp/scenarios.hidden /app/scenarios; fi
if [ -d /tmp/tests.hidden ]; then mv /tmp/tests.hidden /tests; fi

# Copy outputs to a staging area with random names to break 1:1 filename derivation
mkdir -p /tmp/agent_outputs
rm -rf /tmp/agent_outputs/*
cp /app/output.*.txt /tmp/agent_outputs/ 2>/dev/null || true

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
