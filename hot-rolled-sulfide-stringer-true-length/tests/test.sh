#!/bin/bash
mkdir -p /logs/verifier
set +e
# Only solver-invoking tests gate reward. Property checks (naive-fail invariants)
# are kept in test_task_properties.py for audit and do NOT affect reward.
python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA -k "test_script_exists or test_from_scratch or test_heldout_secure or test_randomized_extra"
if [ $? -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
