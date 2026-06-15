"""Run each scenario, diff its output against the matching expected file."""
from pathlib import Path

import pytest

EXPECTED_DIR = Path("/tests/expected")
APP_DIR = Path("/app")

def scenario_names():
    return sorted(p.stem.removesuffix(".expected") for p in EXPECTED_DIR.glob("*.expected.txt"))

@pytest.mark.parametrize("name", scenario_names())
def test_scenario_output_exists(name):
    output = APP_DIR / f"output.{name}.txt"
    assert output.exists(), f"agent did not produce {output}"

@pytest.mark.parametrize("name", scenario_names())
def test_scenario_matches_expected(name):
    output = APP_DIR / f"output.{name}.txt"
    expected = EXPECTED_DIR / f"{name}.expected.txt"
    actual = output.read_text()
    expected_text = expected.read_text()
    assert actual == expected_text, (
        f"[{name}] output mismatch\n"
        f"--- expected ---\n{expected_text}\n"
        f"--- actual ---\n{actual}"
    )
