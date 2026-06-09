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
    "checkpoint_excludes_late_commit": (
        "BEGIN t1\nWRITE t1 a 1\nCHECKPOINT\nCOMMIT t1\n",
        lines("a=1", "CHECKPOINT:"),
    ),
    "savepoint_rollback_partial": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nROLLBACK_TO t1 s1\nCOMMIT t1\n",
        lines("a=1", "CHECKPOINT:"),
    ),
    "rollback_then_continue": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nROLLBACK_TO t1 s1\nWRITE t1 c 3\nCOMMIT t1\n",
        lines("a=1", "c=3", "CHECKPOINT:"),
    ),
    "savepoint_persists_after_rollback": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nROLLBACK_TO t1 s1\nWRITE t1 b 99\nROLLBACK_TO t1 s1\nCOMMIT t1\n",
        lines("a=1", "CHECKPOINT:"),
    ),
    "later_savepoints_forgotten_on_rollback": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nSAVEPOINT t1 s2\nWRITE t1 c 3\nROLLBACK_TO t1 s1\nWRITE t1 d 4\nROLLBACK_TO t1 s2\nCOMMIT t1\n",
        lines("a=1", "d=4", "CHECKPOINT:"),
    ),
    "savepoint_overwrite_moves_marker": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nSAVEPOINT t1 s1\nWRITE t1 c 3\nROLLBACK_TO t1 s1\nCOMMIT t1\n",
        lines("a=1", "b=2", "CHECKPOINT:"),
    ),
    "rollback_to_unknown_savepoint_noop": (
        "BEGIN t1\nWRITE t1 a 1\nROLLBACK_TO t1 ghost\nCOMMIT t1\n",
        lines("a=1", "CHECKPOINT:"),
    ),
    "latest_commit_wins": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\nBEGIN t2\nWRITE t2 a 2\nCOMMIT t2\n",
        lines("a=2", "CHECKPOINT:"),
    ),
    "interleaved_commit_and_abort_with_savepoints": (
        "BEGIN t1\nBEGIN t2\nWRITE t1 a 1\nWRITE t2 b 2\nSAVEPOINT t2 s1\nWRITE t2 c 3\nROLLBACK_TO t2 s1\nCOMMIT t1\nABORT t2\n",
        lines("a=1", "CHECKPOINT:"),
    ),
    "begin_reuse_after_close_blocked": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\nBEGIN t1\nWRITE t1 a 99\nCOMMIT t1\n",
        lines("a=1", "CHECKPOINT:"),
    ),
}

@pytest.mark.parametrize("name", list(CASES.keys()))
def test_txlog(name):
    ops, expected = CASES[name]
    assert run_txlog(ops) == expected
