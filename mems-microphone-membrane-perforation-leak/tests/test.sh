#!/bin/bash
# No network at grade time: pytest is baked into image (see Dockerfile).
# Ground truth is geometric volume from _gen.py CONFIGS.
# Hardened verifier: root-owned chmod 700 on /tests + restricted user for agent subprocess (prevents raw libc.open bypass of audit hook)
mkdir -p /logs/verifier
set +e

# Attempt to create restricted user for agent code execution (Flow A isolation)
# This is the Harbor-recommended OS-user recipe: useradd + chmod 700 /tests + su / setuid for agent call
if id -u mems_restricted_user >/dev/null 2>&1; then
  echo "restricted user exists"
else
  # Try useradd (Debian) then adduser fallback
  useradd -M -s /bin/false mems_restricted_user 2>/dev/null || adduser --disabled-password --gecos '' --no-create-home mems_restricted_user 2>/dev/null || true
fi

# Harden /tests: only root can read – raw libc.open as restricted user will fail
# Note: chmod 700 is a no-op on macOS bind mounts, but enforces on Linux cloud runners
if [ -d /tests ]; then
  chown -R root:root /tests 2>/dev/null || true
  chmod -R 700 /tests 2>/dev/null || true
  # But ensure root can still traverse; 700 is enough for root
fi

# Ensure /app and its data are readable by restricted user (needed after setuid drop)
if [ -d /app ]; then
  chmod -R 755 /app 2>/dev/null || true
  # If /app/solve.py exists, make it world readable
  chmod 644 /app/solve.py 2>/dev/null || true
  chmod 644 /app/data/scene.mems 2>/dev/null || true
fi

# /tmp must be writable for restricted user tempdirs (usually 1777)
chmod 1777 /tmp 2>/dev/null || chmod 777 /tmp 2>/dev/null || true

echo "Running verifier as root (tests dir protected, agent subprocess drops to mems_restricted_user)"
python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
RC=$?
if [ $RC -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
exit $RC
