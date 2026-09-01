#!/bin/bash
# Installs test deps and runs the verifier; writes the reward file.
# Reward is derived from ctrf.json via python -I -S to prevent sitecustomize atexit os._exit(0) hack
mkdir -p /logs/verifier
set +e
apt-get update
apt-get install -y curl

curl -LsSf https://astral.sh/uv/0.9.7/install.sh | sh
source $HOME/.local/bin/env

uvx \
  --with pytest==8.4.1 \
  --with pytest-json-ctrf==0.3.5 \
  --with numpy==2.4.6 \
  pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

python3 -I -S << 'PY'
import json, pathlib
ctrf_path = pathlib.Path("/logs/verifier/ctrf.json")
reward_path = pathlib.Path("/logs/verifier/reward.txt")
try:
    data = json.loads(ctrf_path.read_text())
    summary = data.get("results", {}).get("summary", data.get("summary", {}))
    tests = int(summary.get("tests", 0))
    passed = int(summary.get("passed", 0))
    failed = int(summary.get("failed", 0))
    other = int(summary.get("other", 0))
    if tests > 0 and (failed + other) == 0 and passed > 0:
        reward_path.write_text("1")
    else:
        reward_path.write_text("0")
except Exception:
    try:
        reward_path.write_text("0")
    except Exception:
        pass
PY

