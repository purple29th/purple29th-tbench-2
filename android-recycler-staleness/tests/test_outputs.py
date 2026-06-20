"""Verification tests for android-recycler-staleness."""
import subprocess
from pathlib import Path

import pytest

SCENARIO_PATH = Path("/app/scenario.json")
OUTPUT_PATH = Path("/app/output.txt")
EXPECTED_DIR = Path("/tests/expected")

def run_app(scenario_text):
    SCENARIO_PATH.write_text(scenario_text)
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    result = subprocess.run(
        ["bash", "/app/src/run.sh"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"run.sh failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    assert OUTPUT_PATH.exists(), "Agent must produce /app/output.txt"
    return OUTPUT_PATH.read_text()

def load_case(name):
    scenario = (EXPECTED_DIR / f"{name}.scenario.txt").read_text()
    expected = (EXPECTED_DIR / f"{name}.expected.txt").read_text()
    return scenario, expected

CASE_NAMES = [
    "simple_bind_resolve",
    "recycle_invalidates_pending",
    "rebind_to_different_item",
    "rebind_same_item_invalidates_old",
    "new_fetch_after_rebind",
    "two_cells_independent",
    "auto_url_when_no_resolution",
    "tick_processes_only_due",
    "multiple_pending_resolve_in_order",
    "rapid_recycle_and_rebind",
    "interleaved_binds_across_cells",
    "unbound_query_after_recycle",
    "recycle_leak_gated",
    "refetch_first_write_wins",
]

@pytest.mark.parametrize("name", CASE_NAMES)
def test_scenario(name):
    scenario, expected = load_case(name)
    actual = run_app(scenario)
    assert actual == expected, f"Mismatch for {name}\nExpected:\n{expected}\nActual:\n{actual}"
