#!/bin/bash
# No network at grade time: pytest is baked into the image (see environment/Dockerfile).
# Ground truth is the generator's geometric volume (hardcoded from _gen.py CONFIGS)
# for known held-outs, with a stdlib-only intensity-conservation fallback for
# arbitrary scans. No extra packages needed.
mkdir -p /logs/verifier
set +e
python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
if [ $? -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
