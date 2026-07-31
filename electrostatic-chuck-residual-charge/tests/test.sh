#!/bin/bash
# Hardened verifier: root-owned chmod 700 on /tests + restricted user for agent subprocess
mkdir -p /logs/verifier
set +e

if id -u esca_restricted_user >/dev/null 2>&1; then
  echo "restricted user exists"
else
  useradd -M -s /bin/false esca_restricted_user 2>/dev/null || adduser --disabled-password --gecos '' --no-create-home esca_restricted_user 2>/dev/null || true
fi

if [ -d /tests ]; then
  chown -R root:root /tests 2>/dev/null || true
  chmod -R 700 /tests 2>/dev/null || true
fi

if [ -d /app ]; then
  chmod -R 755 /app 2>/dev/null || true
  chmod 644 /app/solve.py 2>/dev/null || true
  chmod 644 /app/data/scene.esca 2>/dev/null || true
fi

chmod 1777 /tmp 2>/dev/null || chmod 777 /tmp 2>/dev/null || true

echo "Running verifier as root (tests dir protected, agent subprocess drops to esca_restricted_user)"
python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
RC=$?
if [ $RC -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
exit $RC
