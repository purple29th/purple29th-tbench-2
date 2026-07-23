#!/bin/bash
# No network at grade time: only pytest is baked into the image (see
# environment/Dockerfile). Ground truth is recomputed independently in pure
# stdlib Python by intensity conservation (reference_volume_mm3), so the test
# never trusts a value baked into the agent's script.
mkdir -p /logs/verifier
set +e
python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
if [ $? -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
