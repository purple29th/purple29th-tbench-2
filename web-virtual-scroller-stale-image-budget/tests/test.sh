#!/bin/bash
mkdir -p /logs/verifier
set +e
python3 -I -S -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
python3 - << 'PY'
import json, pathlib
ctrf_path = pathlib.Path("/logs/verifier/ctrf.json")
reward_path = pathlib.Path("/logs/verifier/reward.txt")
try:
    ctrf = json.loads(ctrf_path.read_text())
    summary = ctrf.get("summary", {})
    tests = summary.get("tests", 0)
    failed = summary.get("failed", 0)
    other = summary.get("other", 0)
    passed = summary.get("passed", 0)
    reward = 1 if (tests > 0 and failed == 0 and other == 0 and passed > 0) else 0
except Exception:
    reward = 0
reward_path.write_text(str(reward))
PY


