"""Verification tests for android-fragment-nested-child-retention."""

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
    assert result.returncode == 0, (
        f"run.sh failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert OUTPUT_PATH.exists(), "Agent must produce /app/output.txt"
    return OUTPUT_PATH.read_text()


def load_case(name):
    scenario = (EXPECTED_DIR / f"{name}.scenario.txt").read_text()
    expected = (EXPECTED_DIR / f"{name}.expected.txt").read_text()
    return scenario, expected


CASE_NAMES = [
    "single_add",
    "child_requires_parent",
    "child_added_with_parent",
    "remove_parent_cascades",
    "hide_downgrades_lifecycle",
    "show_upgrades_lifecycle",
    "replace_restores_child_tree",
    "pop_named_uses_last",
    "pop_missing_is_noop",
    "rotate_retains_vm_child",
    "rotate_drops_non_backstacked",
    "nested_three_levels",
    "hide_parent_downgrades_child",
    "vm_cleared_on_remove",
    "vm_cleared_on_parent_remove",
    "vm_retained_on_replace_restore",
    "set_max_cascades",
    "set_max_blocks_resumed",
    "detach_retains_vm",
    "detach_attach_restores",
    "detach_child_cascade",
    "hide_with_max",
    "replace_with_max_and_child",
    "rotate_with_detach",
    "rotate_child_of_non_bs_parent_dropped",
    "show_propagates_to_children",
]


@pytest.mark.parametrize("name", CASE_NAMES)
def test_scenario(name):
    scenario, expected = load_case(name)
    actual = run_app(scenario)
    assert actual.strip() == expected.strip(), (
        f"Mismatch for {name}\nExpected:\n{expected}\nActual:\n{actual}"
    )
