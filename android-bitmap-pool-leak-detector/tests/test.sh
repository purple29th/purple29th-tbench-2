#!/bin/bash
set +e
mkdir -p /logs/verifier
cd /app
rm -f /app/output.*.txt /app/output.txt
if [ -d /tests ]; then mv /tests /tmp/tests.hidden; fi
if [ -d /app/scenarios ]; then mv /app/scenarios /tmp/scenarios.hidden; fi
mkdir -p /app/scenarios
cp -a /tmp/scenarios.hidden/*.txt /app/scenarios/ 2>/dev/null || true
kotlinc src/com/example/bitmappool/*.kt -include-runtime -d /app/sim.jar \
    >> /logs/verifier/build.log 2>&1
build_status=$?
if [ $build_status -ne 0 ]; then
    echo "build failed (status $build_status) failing closed" >> /logs/verifier/build.log
    echo 0 > /logs/verifier/reward.txt
    if [ -d /tmp/tests.hidden ]; then mv /tmp/tests.hidden /tests; fi
    if [ -d /tmp/scenarios.hidden ]; then rm -rf /app/scenarios; mv /tmp/scenarios.hidden /app/scenarios; fi
    exit 0
fi
for scenario_file in /app/scenarios/*.txt; do
    name=$(basename "$scenario_file" .txt)
    java -jar /app/sim.jar "$scenario_file" "/app/output.${name}.txt" \
        >> /logs/verifier/run.log 2>&1
done
if [ -d /tmp/tests.hidden ]; then mv /tmp/tests.hidden /tests; fi
if [ -d /tmp/scenarios.hidden ]; then rm -rf /app/scenarios; mv /tmp/scenarios.hidden /app/scenarios; fi
uvx --python 3.12 --with pytest==8.4.1 \
    pytest /tests/test_outputs.py -rA --tb=short \
    > /logs/verifier/test-stdout.txt 2>&1
status=$?
if [ $status -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
exit 0
