#!/bin/bash
set -euo pipefail
cd /app
if [ ! -f build/app.jar ]; then
    bash src/build.sh
fi
kotlin -cp build/app.jar com.example.app.MainKt
