#!/bin/bash
set -euo pipefail
cd /app
if [ ! -f build/app.jar ]; then bash src/build.sh; fi
output=$(java -cp build/app.jar:/opt/kotlinc/lib/kotlin-stdlib.jar com.example.fragment.test.ManagerContractKt 2>&1)
echo "$output"
if echo "$output" | grep -q "^FAIL"; then
  echo "Contract tests failed"
  exit 1
fi
