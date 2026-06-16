"""Run each scenario, diff its output against the matching expected file."""
from pathlib import Path

import pytest

EXPECTED_DIR = Path("/tests/expected")
APP_DIR = Path("/app")

def scenario_names() -> list[str]:
    return sorted(p.stem.removesuffix(".expected") for p in EXPECTED_DIR.glob("*.expected.txt"))

@pytest.mark.parametrize("name", scenario_names())
def test_scenario_output_exists(name: str) -> None:
    output = APP_DIR / f"output.{name}.txt"
    assert output.exists(), f"agent did not produce {output}"

@pytest.mark.parametrize("name", scenario_names())
def test_scenario_matches_expected(name: str) -> None:
    actual = (APP_DIR / f"output.{name}.txt").read_text()
    expected = (EXPECTED_DIR / f"{name}.expected.txt").read_text()
    assert actual == expected, (
        f"[{name}] output mismatch\n--- expected ---\n{expected}\n--- actual ---\n{actual}"
    )
