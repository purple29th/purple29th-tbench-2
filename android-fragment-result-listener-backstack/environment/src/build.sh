#!/bin/bash
set -euo pipefail
cd /app
rm -rf build
mkdir -p build
kotlinc -d build/app.jar $(find src -name '*.kt')
