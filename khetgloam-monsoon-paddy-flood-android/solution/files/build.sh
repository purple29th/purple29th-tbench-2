#!/bin/bash
# Builds all required artifacts into /app:
#   - risk.comp.spv        compiled SPIR-V compute shader
#   - libvkflood_host.so   host x86-64 raw-Vulkan JNI lib (for verification on lavapipe)
#   - vkflood.aar          Android library packaging the arm64-v8a raw-Vulkan JNI lib
set -euo pipefail
cd /app

SHADER=vkflood/src/main/cpp/shaders/risk.comp

# 1. Compile the compute shader -> SPIR-V artifact + embedded C header.
glslangValidator -V --target-env vulkan1.0 -o /app/risk.comp.spv "${SHADER}"
glslangValidator -V --target-env vulkan1.0 --vn risk_spv \
    -o vkflood/src/main/cpp/risk_spv.h "${SHADER}"

# 2. Host x86-64 JNI lib (raw Vulkan on host / lavapipe).
cmake -S host -B host/build -DCMAKE_BUILD_TYPE=Release
cmake --build host/build -j
cp host/build/libvkflood_host.so /app/libvkflood_host.so

# 3. Android AAR (arm64-v8a raw-Vulkan lib) via Gradle, built `--offline`: the AGP +
#    aapt2 + lint-gradle/groovy deps are pre-warmed into the image's Gradle cache,
#    so we never touch the (ratelimited) Maven proxy at solve time. A DEBUG aar is
#    built (matches the prewarm); the arm64 native lib links the NDK's libvulkan.
gradle --no-daemon --offline :vkflood:assembleDebug
AAR="$(find vkflood/build/outputs/aar -name '*.aar' | head -1)"
cp "${AAR}" /app/vkflood.aar

echo "built:"
ls -la /app/libvkflood_host.so /app/risk.comp.spv /app/vkflood.aar
