"""Verification tests for transaction-log-replay."""
import subprocess

import pytest

TXLOG = "/app/txlog"

def run_txlog(ops):
    proc = subprocess.run(
        [TXLOG],
        input=ops,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, f"txlog exited {proc.returncode}; stderr:\n{proc.stderr}"
    return proc.stdout

def lines(*entries):
    return "".join(line + "\n" for line in entries)

CASES = {
    "basic_commit": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\n",
        lines("a=1", "CHECKPOINT:"),
    ),
    "abort_discards_writes": (
        "BEGIN t1\nWRITE t1 a 1\nABORT t1\n",
        lines("CHECKPOINT:"),
    ),
    "uncommitted_invisible_to_checkpoint": (
        "BEGIN t1\nWRITE t1 a 1\nCHECKPOINT\n",
        lines("CHECKPOINT:"),
    ),
    "checkpoint_excludes_late_commit": (
        "BEGIN t1\nWRITE t1 a 1\nCHECKPOINT\nCOMMIT t1\n",
        lines("a=1", "CHECKPOINT:"),
    ),
    "checkpoint_includes_committed_only": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\nBEGIN t2\nWRITE t2 b 2\nCHECKPOINT\nCOMMIT t2\n",
        lines("a=1", "b=2", "CHECKPOINT:", "a=1"),
    ),
    "multiple_checkpoints_keep_latest": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\nCHECKPOINT\nBEGIN t2\nWRITE t2 b 2\nCOMMIT t2\nCHECKPOINT\n",
        lines("a=1", "b=2", "CHECKPOINT:", "a=1", "b=2"),
    ),
    "latest_commit_wins": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\nBEGIN t2\nWRITE t2 a 2\nCOMMIT t2\n",
        lines("a=2", "CHECKPOINT:"),
    ),
    "abort_after_multiple_writes_total": (
        "BEGIN t1\nWRITE t1 a 1\nWRITE t1 a 2\nWRITE t1 b 3\nABORT t1\n",
        lines("CHECKPOINT:"),
    ),
    "interleaved_commit_and_abort": (
        "BEGIN t1\nBEGIN t2\nWRITE t1 a 1\nWRITE t2 b 2\nCOMMIT t1\nABORT t2\n",
        lines("a=1", "CHECKPOINT:"),
    ),
    "write_after_commit_ignored": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\nWRITE t1 a 99\n",
        lines("a=1", "CHECKPOINT:"),
    ),
    "double_commit_is_noop": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\nCOMMIT t1\n",
        lines("a=1", "CHECKPOINT:"),
    ),
    "empty_input": (
        "",
        lines("CHECKPOINT:"),
    ),
}

@pytest.mark.parametrize("name", list(CASES.keys()))
def test_txlog(name):
    ops, expected = CASES[name]
    assert run_txlog(ops) == expected
