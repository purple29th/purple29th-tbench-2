"""Verification tests for android-fragment-result-listener-backstack."""

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
    "simple_add",
    "listener_registration",
    "result_delivered_when_listener_exists",
    "result_queued_when_no_listener",
    "pending_delivered_when_listener_added_later",
    "clear_listener",
    "remove_clears_listeners_and_pending",
    "replace_captures_result_state",
    "pop_named_uses_last",
    "pop_missing_is_noop",
    "rotate_retains_listeners_and_pending_for_backstacked",
    "rotate_drops_non_backstacked_result",
    "queued_result_survives_rotate_if_backstacked",
    "anon_backstack_label",
    "multi_query_blank_line",
    # expanded coverage per review
    "pending_overwrite",
    "ignore_missing_fragment",
    "case_sensitive_pop",
    "case_sensitive_pop_noop",
    "multi_container_sorting",
    "multiple_keys",
    "remove_pop_restore_result",
    "rotate_mixed_backstacked_non",
    "pending_multiple_keys_overwrite",
]


@pytest.mark.parametrize("name", CASE_NAMES)
def test_scenario(name):
    scenario, expected = load_case(name)
    actual = run_app(scenario)
    assert actual.strip() == expected.strip(), (
        f"Mismatch for {name}\nExpected:\n{expected}\nActual:\n{actual}"
    )
