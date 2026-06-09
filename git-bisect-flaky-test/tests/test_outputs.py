"""Verify the agent identified the regression commit and diagnosed it."""
import re
import subprocess
from pathlib import Path

import pytest

ANSWER_PATH = Path("/app/answer.txt")
REPO_PATH = Path("/app/repo")
HELPER_PATH = "/usr/local/bin/flake-rate"
HIGH_RATE_THRESHOLD = 0.5

DIAGNOSIS_KEYWORDS = ("settle", "recipients", "divisor", "platform", "fee")
MIN_KEYWORDS_REQUIRED = 2
SHA_PATTERN = re.compile(r"^[0-9a-f]{7,40}$")
BUG_MECHANISM_PATTERNS = (
    r"\+\s*1",
    r"plus one",
    r"off[- ]by[- ]one",
    r"recipients\s*\+\s*1",
    r"extra recipient",
    r"one too many",
)

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

def lookup_flake_rate(sha):
    result = subprocess.run(
        [HELPER_PATH, sha],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0

def find_first_high_rate_commit():
    log = git("log", "--reverse", "--format=%H").stdout.strip().splitlines()
    for sha in log:
        if lookup_flake_rate(sha) >= HIGH_RATE_THRESHOLD:
            return sha
    return ""

def keyword_hits(text):
    lowered = text.lower()
    return [kw for kw in DIAGNOSIS_KEYWORDS if kw in lowered]

def mechanism_mentioned(text):
    lowered = text.lower()
    return any(re.search(pat, lowered) for pat in BUG_MECHANISM_PATTERNS)

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
    expected = find_first_high_rate_commit()
    assert actual and expected, "could not resolve commit hashes"
    assert actual == expected, f"wrong commit: {actual[:12]} vs {expected[:12]}"

def test_diagnosis_has_keywords(answer_lines):
    assert len(answer_lines) >= 2, "answer.txt missing diagnosis line"
    diagnosis = " ".join(answer_lines[1:])
    hits = keyword_hits(diagnosis)
    assert len(hits) >= MIN_KEYWORDS_REQUIRED, (
        f"diagnosis must mention at least {MIN_KEYWORDS_REQUIRED} of {DIAGNOSIS_KEYWORDS}; got {hits}"
    )

def test_diagnosis_describes_mechanism(answer_lines):
    diagnosis = " ".join(answer_lines[1:])
    assert mechanism_mentioned(diagnosis), (
        "diagnosis must describe the bug mechanism (off-by-one, +1, extra recipient, etc.)"
    )
