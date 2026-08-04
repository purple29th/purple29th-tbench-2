#!/bin/bash
set -euo pipefail
cd /app
rm -rf build
mkdir -p build
/opt/kotlinc/bin/kotlinc -d build/app.jar $(find src -name "*.kt" | tr '\n' ' ')
echo "built app.jar"
