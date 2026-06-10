#!/bin/bash
set -euo pipefail
cd /app
mkdir -p build
kotlinc -d build/app.jar $(find src -name '*.kt')
kotlin -cp build/app.jar com.example.theme.test.ResolverContractKt
