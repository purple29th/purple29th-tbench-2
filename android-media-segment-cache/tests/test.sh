#!/bin/bash
set +e
mkdir -p /logs/verifier
cd /app
# Reward integrity: clear any pre-existing outputs so a non-compiling submission
# cannot pass on stale /app/output.*.txt files left in the working tree.
rm -f /app/output.*.txt
kotlinc src/com/example/mediacache/*.kt -include-runtime -d /app/sim.jar \
    >> /logs/verifier/build.log 2>&1
build_status=$?
if [ $build_status -ne 0 ]; then
    echo "build failed (status $build_status) — failing closed" >> /logs/verifier/build.log
    echo 0 > /logs/verifier/reward.txt
    exit 0
fi
for scenario_file in /app/scenarios/*.txt; do
    name=$(basename "$scenario_file" .txt)
    java -jar /app/sim.jar "$scenario_file" "/app/output.${name}.txt" \
        >> /logs/verifier/run.log 2>&1
done
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
