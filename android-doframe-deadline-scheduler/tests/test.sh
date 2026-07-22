#!/bin/bash
set +e
mkdir -p /logs/verifier

# ---------- Anti-cheat hardening ----------
# The agent's compiled jar runs as root in the same filesystem as /tests at grade time.
# Prior fix moved /tests to /tmp/tests.hidden which is still world-readable and walkable by root.
# Also /app/scenarios/<name>.txt and /app/output.<name>.txt leak the scenario stem via /proc/self/cmdline.
# To close both:
#   1. Bundle /tests into a shell variable and rm -rf /tests so no expected file exists on disk during agent run.
#      Variable is not exported, so not in /proc/*/environ and not on filesystem.
#   2. Bundle /app/scenarios into a variable, rm -rf, then recreate under randomized UUID filenames.
#      Map UUID->name stays in shell memory only.
#   3. After agent run, restore /tests from bundle and translate UUID outputs to named outputs for pytest.

EXPECTED_BUNDLE=""
if [ -d /tests ]; then
    EXPECTED_BUNDLE=$(tar czf - -C / tests 2>/dev/null | base64 -w0)
    rm -rf /tests
fi

SCENARIOS_BUNDLE=""
if [ -d /app/scenarios ]; then
    SCENARIOS_BUNDLE=$(tar czf - -C / app/scenarios 2>/dev/null | base64 -w0)
    rm -rf /app/scenarios
fi

mkdir -p /app/scenarios
MAPPING=""
TMP_SCEN_DIR="/tmp/_scen_orig"
rm -rf "$TMP_SCEN_DIR"
mkdir -p "$TMP_SCEN_DIR"

# Restore original scenarios to temp dir for iteration
if [ -n "$SCENARIOS_BUNDLE" ]; then
    echo "$SCENARIOS_BUNDLE" | base64 -d | tar xzf - -C /tmp 2>/dev/null
    # tar created /tmp/app/scenarios
    if [ -d /tmp/app/scenarios ]; then
        mv /tmp/app/scenarios/* "$TMP_SCEN_DIR"/ 2>/dev/null || true
        rm -rf /tmp/app
    fi
else
    # Fallback if bundle empty (local dev without /app/scenarios pre-existing)
    mkdir -p "$TMP_SCEN_DIR"
fi

# Create randomized UUID copies in /app/scenarios
for f in "$TMP_SCEN_DIR"/*.txt; do
    [ -e "$f" ] || continue
    name=$(basename "$f" .txt)
    uuid=$(cat /proc/sys/kernel/random/uuid)
    cp "$f" "/app/scenarios/$uuid.txt"
    MAPPING="${MAPPING}${uuid} ${name}\n"
done
rm -rf "$TMP_SCEN_DIR"

# ---------- Build ----------
cd /app
rm -f /app/output.*.txt /app/output.*.log
kotlinc src/com/example/choreographer/*.kt -include-runtime -d /app/sim.jar \
    >> /logs/verifier/build.log 2>&1
build_status=$?

if [ $build_status -ne 0 ]; then
    echo "build failed (status $build_status) — failing closed" >> /logs/verifier/build.log
    echo 0 > /logs/verifier/reward.txt
    # Restore for completeness before exit
    rm -rf /app/scenarios
    if [ -n "$SCENARIOS_BUNDLE" ]; then
        echo "$SCENARIOS_BUNDLE" | base64 -d | tar xzf - -C / 2>/dev/null
    fi
    if [ -n "$EXPECTED_BUNDLE" ]; then
        echo "$EXPECTED_BUNDLE" | base64 -d | tar xzf - -C / 2>/dev/null
    fi
    exit 0
fi

# ---------- Run agent against randomized scenario names ----------
for scenario_file in /app/scenarios/*.txt; do
    [ -e "$scenario_file" ] || continue
    uuid=$(basename "$scenario_file" .txt)
    java -jar /app/sim.jar "$scenario_file" "/app/output.${uuid}.txt" \
        >> /logs/verifier/run.log 2>&1
done

cp /app/output.*.txt /logs/verifier/ 2>/dev/null || true
# Remove randomized scenario dir, restore originals and tests before pytest
rm -rf /app/scenarios
if [ -n "$SCENARIOS_BUNDLE" ]; then
    echo "$SCENARIOS_BUNDLE" | base64 -d | tar xzf - -C / 2>/dev/null
fi
if [ -n "$EXPECTED_BUNDLE" ]; then
    echo "$EXPECTED_BUNDLE" | base64 -d | tar xzf - -C / 2>/dev/null
fi

# Translate UUID outputs -> named outputs for pytest
# MAPPING lines: "<uuid> <name>"
printf "%b" "$MAPPING" | while IFS= read -r line; do
    [ -z "$line" ] && continue
    uuid=$(echo "$line" | awk '{print $1}')
    name=$(echo "$line" | awk '{print $2}')
    if [ -n "$uuid" ] && [ -n "$name" ] && [ -f "/app/output.$uuid.txt" ]; then
        cp "/app/output.$uuid.txt" "/app/output.$name.txt"
    fi
done

# Clean up UUID outputs (keep only named for pytest)
for f in /app/output.*.txt; do
    [ -e "$f" ] || continue
    base=$(basename "$f")
    # if filename looks like output.<uuid>.txt (uuid contains dashes), remove if not matching known scenario name
    # We keep files whose name part exists in original scenarios
    # Simpler: delete files where second field has 4 dashes (uuid pattern) and keep others
    if echo "$base" | grep -Eq "output\.[0-9a-f]{8}-"; then
        rm -f "$f"
    fi
done

# ---------- Verify ----------
uvx --python 3.12 --with pytest==8.3.3 \
    pytest /tests/test_outputs.py -rA --tb=short \
    > /logs/verifier/test-stdout.txt 2>&1
status=$?

if [ $status -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi

exit 0
