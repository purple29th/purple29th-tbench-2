"""Verification tests for android-theme-cascade."""
import json
import subprocess
from pathlib import Path

import pytest

SCENARIO_PATH = Path("/app/scenario.json")
OUTPUT_PATH = Path("/app/output.json")
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
    assert OUTPUT_PATH.exists(), "Agent must produce /app/output.json"
    return json.loads(OUTPUT_PATH.read_text())

def load_case(name):
    scenario = (EXPECTED_DIR / f"{name}.scenario.json").read_text()
    expected = json.loads((EXPECTED_DIR / f"{name}.expected.json").read_text())
    return scenario, expected

CASE_NAMES = [
    "child_overrides_parent",
    "component_override_beats_theme",
    "state_override_only_in_state",
    "default_state_unaffected_by_pressed_override",
    "explicit_apply_survives_switch",
    "unbound_follows_switch",
    "multiple_switches_unbound_follows_latest",
    "explicit_apply_through_two_switches",
    "state_override_beats_component_override",
    "deep_inheritance_three_levels",
    "multiple_components_independent",
    "mixed_apply_and_unbound",
]

@pytest.mark.parametrize("name", CASE_NAMES)
def test_scenario(name):
    scenario, expected = load_case(name)
    actual = run_app(scenario)
    assert actual == expected, f"Mismatch for {name}\nExpected:\n{json.dumps(expected, indent=2)}\nActual:\n{json.dumps(actual, indent=2)}"
