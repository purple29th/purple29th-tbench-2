"""Run each scenario, diff its output against the matching expected file."""
from pathlib import Path

import pytest

EXPECTED_DIR = Path("/tests/expected")
APP_DIR = Path("/app")

def scenario_names() -> list[str]:
    return sorted(p.stem.removesuffix(".expected") for p in EXPECTED_DIR.glob("*.expected.txt"))

def output_path_for(name: str) -> Path:
    return APP_DIR / f"output.{name}.txt"

def expected_path_for(name: str) -> Path:
    return EXPECTED_DIR / f"{name}.expected.txt"

@pytest.mark.parametrize("name", scenario_names())
def test_scenario_output_exists(name: str) -> None:
    output = output_path_for(name)
    assert output.exists(), f"agent did not produce {output}"

@pytest.mark.parametrize("name", scenario_names())
def test_scenario_matches_expected(name: str) -> None:
    actual = output_path_for(name).read_text()
    expected = expected_path_for(name).read_text()
    assert actual == expected, (
        f"[{name}] output mismatch\n--- expected ---\n{expected}\n--- actual ---\n{actual}"
    )
