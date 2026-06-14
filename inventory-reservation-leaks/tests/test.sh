#!/bin/bash
set +e
mkdir -p /logs/verifier

cd /app
kotlinc src/com/example/inventory/*.kt -include-runtime -d /app/sim.jar \
    >> /logs/verifier/build.log 2>&1
build_status=$?

if [ $build_status -eq 0 ]; then
    java -jar /app/sim.jar >> /logs/verifier/run.log 2>&1
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
