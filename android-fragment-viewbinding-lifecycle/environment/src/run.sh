#!/bin/bash
set -euo pipefail
cd /app
rm -rf build
bash src/build.sh
java -cp build/app.jar:/opt/kotlinc/lib/kotlin-stdlib.jar com.example.app.MainKt
