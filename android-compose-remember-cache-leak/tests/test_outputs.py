"""Verification for android-compose-remember-cache-leak"""

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
    assert OUTPUT_PATH.exists(), "must produce /app/output.txt"
    return OUTPUT_PATH.read_text()


def load_case(name):
    scenario = (EXPECTED_DIR / f"{name}.scenario.txt").read_text()
    expected = (EXPECTED_DIR / f"{name}.expected.txt").read_text()
    return scenario, expected


CASE_NAMES = [
    "mount_put_query",
    "update_clears_remember_vm_survives",
    "child_cascade_update",
    "unmount_clears_descendants",
    "same_key_no_clear",
    "remount_after_unmount",
    "deep_nesting_cascade",
    "vm_survives_update_remember_cleared",
    "vm_cleared_on_unmount",
    "mount_ignored_missing_parent",
    "multiple_children_cascade",
    "interleaved_mount_update",
    "hide_show_cascade",
    "rotate_clears_remember",
    "parent_in_same_txn",
    "backstack_pop",
]


@pytest.mark.parametrize("name", CASE_NAMES)
def test_scenario(name):
    scenario, expected = load_case(name)
    actual = run_app(scenario)
    assert actual.strip() == expected.strip(), (
        f"Mismatch for {name}\nExpected:\n{expected}\nActual:\n{actual}"
    )
