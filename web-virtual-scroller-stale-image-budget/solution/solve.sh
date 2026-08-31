#!/bin/bash
set -euo pipefail
# Find solution files
SOL_DIR="/solution"
if [ ! -d "$SOL_DIR" ]; then
  SOL_DIR="$(pwd)/solution"
fi
if [ ! -d "$SOL_DIR" ]; then
  SOL_DIR="/app/solution"
fi
if [ ! -d "$SOL_DIR" ]; then
  SOL_DIR="/tmp/web_oracle/solution"
fi
# Copy fixed files to /app/src if exists, else to relative
APP_SRC="/app/src"
if [ ! -d "$APP_SRC" ]; then
  APP_SRC="$(pwd)/../environment/src"
fi
if [ ! -d "$APP_SRC" ]; then
  APP_SRC="/tmp/web_oracle/app/src"
fi
echo "Copying from $SOL_DIR to $APP_SRC"
cp "$SOL_DIR/pool.py" "$APP_SRC/pool.py" 2>/dev/null || cp "$(pwd)/pool.py" "$APP_SRC/pool.py" || true
cp "$SOL_DIR/scheduler.py" "$APP_SRC/scheduler.py" 2>/dev/null || cp "$(pwd)/scheduler.py" "$APP_SRC/scheduler.py" || true
# Also copy to current app/src if in docker
if [ -d "/app/src" ]; then
  cp "$SOL_DIR/pool.py" /app/src/pool.py
  cp "$SOL_DIR/scheduler.py" /app/src/scheduler.py
fi
# Run main with scenario
if [ -f "/app/scenario.json" ]; then
  python3 /app/src/main.py < /app/scenario.json > /app/output.txt || true
  cat /app/output.txt || true
fi
