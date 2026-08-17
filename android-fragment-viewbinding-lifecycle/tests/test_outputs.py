"""Verification tests for android-fragment-viewbinding-lifecycle."""

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
    "simple_add_binding_empty",
    "bind_put",
    "hide_clears_binding",
    "hide_show_binding_recreated_empty",
    "viewModel_retained_across_hide_binding_not",
    "detach_clears_binding_retains_vm",
    "detach_attach_binding_empty_vm_retained",
    "hide_propagates_binding_clear_to_children",
    "show_propagates_binding_empty_to_children",
    "rotate_clears_binding_retains_vm_savedState",
    "rotate_drops_non_backstacked_binding",
    "pop_named_uses_last",
    "pop_missing_is_noop",
    "replace_clears_binding_of_old",
    "replace_child_binding_cleared_on_parent_replace",
    "set_max_cascades_binding_retained",
    "hide_propagates_three_levels",
    "pop_restore_viewModel_retained",
    "rotate_child_orphan_dropped",
    # additional coverage per review
    "remove_clears_descendants",
    "add_child_ignored_when_parent_detached",
    "pop_anonymous_uses_last",
    "rotate_backstacked_replace",
    "rotate_backstacked_hide",
    "rotate_backstacked_set_max",
    "remove_pop_restore",
]


@pytest.mark.parametrize("name", CASE_NAMES)
def test_scenario(name):
    scenario, expected = load_case(name)
    actual = run_app(scenario)
    assert actual.strip() == expected.strip(), (
        f"Mismatch for {name}\nExpected:\n{expected}\nActual:\n{actual}"
    )
