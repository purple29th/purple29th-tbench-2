#!/bin/bash
mkdir -p /logs/verifier
set +e
# Only solver-invoking tests gate reward. Property checks (naive-fail invariants)
# are kept in test_task_properties.py for audit and do NOT affect reward.
python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA -k "test_script_exists or test_from_scratch or test_heldout_secure or test_randomized_extra"
python3 -I -S << 'PY'
import json
import pathlib
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

