#!/bin/bash
set +e
mkdir -p /logs/verifier

cd /app
kotlinc src/com/example/bitmappool/*.kt -include-runtime -d /app/sim.jar \
    >> /logs/verifier/build.log 2>&1
build_status=$?

if [ $build_status -eq 0 ]; then
    for scenario_file in /app/scenarios/*.txt; do
        name=$(basename "$scenario_file" .txt)
        java -jar /app/sim.jar "$scenario_file" "/app/output.${name}.txt" \
            >> /logs/verifier/run.log 2>&1
    done
fi

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
