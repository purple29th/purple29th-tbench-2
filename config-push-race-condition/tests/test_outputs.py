"""Verify the config-store simulator output matches the expected log."""
from pathlib import Path

OUTPUT = Path("/app/output.txt")
EXPECTED = Path("/tests/expected.txt")

def test_output_exists():
    assert OUTPUT.exists(), "agent did not produce /app/output.txt"

def test_output_matches_expected():
    actual = OUTPUT.read_text()
    expected = EXPECTED.read_text()
    assert actual == expected, (
        f"output mismatch\n--- expected ---\n{expected}\n--- actual ---\n{actual}"
    )
