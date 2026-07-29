#!/bin/bash
set -euo pipefail
# copy solution to /app for verifier
cp /solution/solve.py /app/solve.py
python3 /app/solve.py /app/data/scene.udel
