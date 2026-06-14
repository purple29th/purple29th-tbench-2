"""Verification tests for android-fragment-backstack-replay."""
import subprocess
from pathlib import Path

import pytest

SCENARIO_PATH = Path("/app/scenario.txt")
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
    "single_add",
    "pop_unnamed_restores_replaced",
    "pop_named_drops_through",
    "pop_missing_name_is_noop",
    "rotate_drops_non_backstacked",
    "rotate_replays_backstacked",
    "anon_backstack_entry",
    "remove_within_transaction",
    "multiple_containers",
    "rotate_then_pop",
    "back_stack_then_anon_then_named_pop",
    "replace_on_empty_after_rotate",
]

@pytest.mark.parametrize("name", CASE_NAMES)
def test_scenario(name):
    scenario, expected = load_case(name)
    actual = run_app(scenario)
    assert actual == expected, f"Mismatch for {name}\nExpected:\n{expected}\nActual:\n{actual}"
