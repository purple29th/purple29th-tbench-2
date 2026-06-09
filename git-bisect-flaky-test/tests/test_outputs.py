"""Verify the agent identified the regression commit and diagnosed it."""
import re
import subprocess
from pathlib import Path

import pytest

ANSWER_PATH = Path("/app/answer.txt")
REPO_PATH = Path("/app/repo")

DIAGNOSIS_KEYWORDS = ("settle", "recipients", "divisor")
MIN_KEYWORDS_REQUIRED = 2
SHA_PATTERN = re.compile(r"^[0-9a-f]{7,40}$")

def read_answer_lines():
    return ANSWER_PATH.read_text().strip().splitlines()

def git(*args):
    return subprocess.run(
        ["git", *args],
        cwd=str(REPO_PATH),
        capture_output=True,
        text=True,
    )

def resolve_full_sha(short_sha):
    result = git("rev-parse", short_sha)
    return result.stdout.strip() if result.returncode == 0 else ""

def find_flake_rate_change_commit():
    log = git("log", "--all", "--format=%H").stdout.strip().splitlines()
    for sha in log:
        diff = git("show", "--format=", "--unified=0", sha, "--", ".flake_rate").stdout
        if "+0.95" in diff and "-0.30" in diff:
            return sha
    return ""

def keyword_hits(text):
    lowered = text.lower()
    return [kw for kw in DIAGNOSIS_KEYWORDS if kw in lowered]

@pytest.fixture(scope="module")
def answer_lines():
    assert ANSWER_PATH.exists(), "Agent must write /app/answer.txt"
    return read_answer_lines()

def test_answer_file_present():
    assert ANSWER_PATH.exists()

def test_first_line_is_sha(answer_lines):
    assert answer_lines, "answer.txt is empty"
    assert SHA_PATTERN.match(answer_lines[0]), f"first line not a git SHA: {answer_lines[0]!r}"

def test_sha_matches_regression_commit(answer_lines):
    actual = resolve_full_sha(answer_lines[0])
    expected = find_flake_rate_change_commit()
    assert actual and expected, "could not resolve commit hashes"
    assert actual == expected, f"wrong commit: {actual[:12]} vs {expected[:12]}"

def test_diagnosis_present(answer_lines):
    assert len(answer_lines) >= 2, "answer.txt missing diagnosis line"
    diagnosis = " ".join(answer_lines[1:])
    hits = keyword_hits(diagnosis)
    assert len(hits) >= MIN_KEYWORDS_REQUIRED, (
        f"diagnosis must mention at least {MIN_KEYWORDS_REQUIRED} of {DIAGNOSIS_KEYWORDS}; got {hits}"
    )
