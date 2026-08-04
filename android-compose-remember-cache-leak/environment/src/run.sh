#!/bin/bash
set -euo pipefail
cd /app
if [ ! -f build/app.jar ]; then bash src/build.sh; fi
java -cp build/app.jar:/opt/kotlinc/lib/kotlin-stdlib.jar com.example.app.MainKt
