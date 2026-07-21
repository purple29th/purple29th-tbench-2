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
    assert proc.returncode == 0, (
        f"txlog exited {proc.returncode}; stderr:\n{proc.stderr}"
    )
    return proc.stdout


def _norm(s):
    body = s.replace("\r\n", "\n").rstrip("\n")
    return "\n".join(line.rstrip() for line in body.split("\n"))


CASES = {
    "basic_commit": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\n",
        "a=1\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "abort_discards_writes": (
        "BEGIN t1\nWRITE t1 a 1\nABORT t1\n",
        "CHECKPOINT:\nCONFLICTS:\n",
    ),
    "checkpoint_excludes_late_commit": (
        "BEGIN t1\nWRITE t1 a 1\nCHECKPOINT\nCOMMIT t1\n",
        "a=1\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "savepoint_rollback_partial": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nROLLBACK_TO t1 s1\nCOMMIT t1\n",
        "a=1\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "rollback_then_continue": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nROLLBACK_TO t1 s1\nWRITE t1 c 3\nCOMMIT t1\n",
        "a=1\nc=3\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "savepoint_persists_after_rollback": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nROLLBACK_TO t1 s1\nWRITE t1 b 99\nROLLBACK_TO t1 s1\nCOMMIT t1\n",
        "a=1\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "later_savepoints_forgotten_on_rollback": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nSAVEPOINT t1 s2\nWRITE t1 c 3\nROLLBACK_TO t1 s1\nWRITE t1 d 4\nROLLBACK_TO t1 s2\nCOMMIT t1\n",
        "a=1\nd=4\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "savepoint_overwrite_moves_marker": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nSAVEPOINT t1 s1\nWRITE t1 c 3\nROLLBACK_TO t1 s1\nCOMMIT t1\n",
        "a=1\nb=2\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "rollback_to_unknown_savepoint_noop": (
        "BEGIN t1\nWRITE t1 a 1\nROLLBACK_TO t1 ghost\nCOMMIT t1\n",
        "a=1\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "sequential_last_writer_wins": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\nBEGIN t2\nWRITE t2 a 2\nCOMMIT t2\n",
        "a=2\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "begin_reuse_after_close_blocked": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\nBEGIN t1\nWRITE t1 a 99\nCOMMIT t1\n",
        "a=1\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "conflict_first_committer_wins": (
        "BEGIN t1\nBEGIN t2\nWRITE t1 a 1\nWRITE t2 a 2\nCOMMIT t1\nCOMMIT t2\n",
        "a=1\nCHECKPOINT:\nCONFLICTS:\nt2\n",
    ),
    "no_conflict_disjoint_keys": (
        "BEGIN t1\nBEGIN t2\nWRITE t1 a 1\nWRITE t2 b 2\nCOMMIT t1\nCOMMIT t2\n",
        "a=1\nb=2\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "conflict_rejects_whole_tx": (
        "BEGIN t1\nBEGIN t2\nWRITE t1 a 1\nWRITE t1 b 1\nWRITE t2 b 2\nWRITE t2 c 2\nCOMMIT t1\nCOMMIT t2\n",
        "a=1\nb=1\nCHECKPOINT:\nCONFLICTS:\nt2\n",
    ),
    "rolledback_write_not_in_conflict_set": (
        "BEGIN t1\nBEGIN t2\nWRITE t1 a 1\nSAVEPOINT t2 s0\nWRITE t2 a 2\nROLLBACK_TO t2 s0\nWRITE t2 d 4\nCOMMIT t1\nCOMMIT t2\n",
        "a=1\nd=4\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "failed_commit_does_not_bump_version": (
        "BEGIN t1\nBEGIN t2\nBEGIN t3\nWRITE t1 a 1\nWRITE t2 a 2\nWRITE t3 a 3\nCOMMIT t1\nCOMMIT t2\nCOMMIT t3\n",
        "a=1\nCHECKPOINT:\nCONFLICTS:\nt2\nt3\n",
    ),
    "abort_then_no_conflict": (
        "BEGIN t1\nBEGIN t2\nWRITE t1 a 1\nWRITE t2 a 2\nABORT t1\nCOMMIT t2\n",
        "a=2\nCHECKPOINT:\nCONFLICTS:\n",
    ),
    "checkpoint_between_conflicting_commits": (
        "BEGIN t1\nBEGIN t2\nWRITE t1 a 1\nWRITE t2 a 2\nCOMMIT t1\nCHECKPOINT\nCOMMIT t2\n",
        "a=1\nCHECKPOINT:\na=1\nCONFLICTS:\nt2\n",
    ),
    "adv_interleave_commits": (
        "BEGIN t1\nBEGIN t2\nWRITE t1 a 1\nWRITE t2 b 2\nSAVEPOINT t1 s1\nWRITE t1 c 3\nBEGIN t3\nWRITE t3 a 9\nCOMMIT t1\nROLLBACK_TO t1 s1\nCOMMIT t3\nCHECKPOINT\nWRITE t2 a 5\nCOMMIT t2\nBEGIN t4\nWRITE t4 d 4\nCOMMIT t4\nCHECKPOINT\n",
        "a=1\nc=3\nd=4\nCHECKPOINT:\na=1\nc=3\nd=4\nCONFLICTS:\nt3\nt2\n",
    ),
    "adv_rollback_shrinks_conflict_set": (
        "BEGIN w1\nWRITE w1 x 1\nCOMMIT w1\nBEGIN r1\nSAVEPOINT r1 base\nWRITE r1 x 99\nWRITE r1 y 2\nBEGIN w2\nWRITE w2 x 7\nCOMMIT w2\nROLLBACK_TO r1 base\nWRITE r1 z 3\nCOMMIT r1\nCHECKPOINT\n",
        "x=7\nz=3\nCHECKPOINT:\nx=7\nz=3\nCONFLICTS:\n",
    ),
    "adv_failed_commit_no_version_bump": (
        "BEGIN a1\nWRITE a1 k 1\nBEGIN a2\nWRITE a2 k 2\nBEGIN a3\nWRITE a3 k 3\nCOMMIT a1\nCOMMIT a2\nCOMMIT a3\nBEGIN a4\nWRITE a4 k 4\nCOMMIT a4\nCHECKPOINT\n",
        "k=4\nCHECKPOINT:\nk=4\nCONFLICTS:\na2\na3\n",
    ),
    "adv_savepoint_churn_long": (
        "BEGIN t\nWRITE t a 1\nSAVEPOINT t s1\nWRITE t b 2\nSAVEPOINT t s2\nWRITE t c 3\nROLLBACK_TO t s1\nWRITE t d 4\nSAVEPOINT t s2\nWRITE t e 5\nROLLBACK_TO t s2\nSAVEPOINT t s1\nWRITE t f 6\nCOMMIT t\nCHECKPOINT\n",
        "a=1\nd=4\nf=6\nCHECKPOINT:\na=1\nd=4\nf=6\nCONFLICTS:\n",
    ),
    "adv_checkpoint_conflict_weave": (
        "BEGIN p\nWRITE p a 1\nCOMMIT p\nCHECKPOINT\nBEGIN q\nBEGIN r\nWRITE q a 2\nWRITE r b 3\nCOMMIT r\nCOMMIT q\nCHECKPOINT\nBEGIN s\nWRITE s a 9\nBEGIN u\nWRITE u a 8\nCOMMIT s\nCOMMIT u\nABORT_NONE\nCHECKPOINT\n",
        "a=9\nb=3\nCHECKPOINT:\na=9\nb=3\nCONFLICTS:\nu\n",
    ),
    "rw_conflict_read_then_other_commits": (
        "BEGIN r\nREAD r a\nBEGIN w\nWRITE w a 5\nCOMMIT w\nWRITE r b 1\nCOMMIT r\nCHECKPOINT\n",
        "a=5\nCHECKPOINT:\na=5\nCONFLICTS:\nr\n",
    ),
    "rollback_undoes_read": (
        "BEGIN r\nSAVEPOINT r base\nREAD r a\nWRITE r b 1\nBEGIN w\nWRITE w a 9\nCOMMIT w\nROLLBACK_TO r base\nWRITE r c 2\nCOMMIT r\nCHECKPOINT\n",
        "a=9\nc=2\nCHECKPOINT:\na=9\nc=2\nCONFLICTS:\n",
    ),
    "read_untouched_key_no_conflict": (
        "BEGIN w\nWRITE w a 1\nCOMMIT w\nBEGIN r\nREAD r z\nWRITE r y 2\nCOMMIT r\nCHECKPOINT\n",
        "a=1\ny=2\nCHECKPOINT:\na=1\ny=2\nCONFLICTS:\n",
    ),
    "adv_serializable_weave": (
        "BEGIN t1\nREAD t1 a\nWRITE t1 b 1\nBEGIN t2\nWRITE t2 a 2\nCOMMIT t2\nCOMMIT t1\nCHECKPOINT\nBEGIN t3\nREAD t3 b\nSAVEPOINT t3 s\nREAD t3 c\nBEGIN t4\nWRITE t4 c 7\nCOMMIT t4\nROLLBACK_TO t3 s\nWRITE t3 d 4\nCOMMIT t3\nCHECKPOINT\nBEGIN t5\nREAD t5 d\nBEGIN t6\nWRITE t6 d 9\nCOMMIT t5\nCOMMIT t6\n",
        "a=2\nc=7\nd=9\nCHECKPOINT:\na=2\nc=7\nd=4\nCONFLICTS:\nt1\n",
    ),
    "adv_gauntlet_full": (
        "BEGIN t1\nWRITE t1 a 1\nSAVEPOINT t1 s1\nWRITE t1 b 2\nBEGIN t2\nWRITE t2 a 5\nSAVEPOINT t2 sp\nWRITE t2 c 3\nCOMMIT t1\nROLLBACK_TO t2 sp\nREAD t2 b\nCOMMIT t2\nCHECKPOINT\nBEGIN t3\nREAD t3 a\nSAVEPOINT t3 base\nWRITE t3 d 4\nBEGIN t4\nWRITE t4 a 9\nCOMMIT t4\nROLLBACK_TO t3 base\nWRITE t3 e 5\nCOMMIT t3\nBEGIN t5\nWRITE t5 f 6\nSAVEPOINT t5 s\nWRITE t5 g 7\nROLLBACK_TO t5 s\nCOMMIT t5\nCHECKPOINT\nBEGIN t6\nREAD t6 e\nBEGIN t7\nWRITE t7 e 9\nCOMMIT t6\nCOMMIT t7\n",
        "a=9\nb=2\ne=9\nf=6\nCHECKPOINT:\na=9\nb=2\nf=6\nCONFLICTS:\nt2\nt3\n",
    ),
    "adv_savepoint_overwrite_weave": (
        "BEGIN t1\nWRITE t1 x 1\nSAVEPOINT t1 s\nWRITE t1 y 2\nSAVEPOINT t1 s\nWRITE t1 z 3\nBEGIN t2\nWRITE t2 x 9\nCOMMIT t1\nCOMMIT t2\nCHECKPOINT\nBEGIN t3\nSAVEPOINT t3 a\nWRITE t3 p 1\nSAVEPOINT t3 b\nWRITE t3 q 2\nROLLBACK_TO t3 a\nSAVEPOINT t3 b\nWRITE t3 r 3\nCOMMIT t3\n",
        "r=3\nx=1\ny=2\nz=3\nCHECKPOINT:\nx=1\ny=2\nz=3\nCONFLICTS:\nt2\n",
    ),
    "adv_read_snapshot_conflict": (
        "BEGIN t1\nWRITE t1 a 1\nCOMMIT t1\nCHECKPOINT\nBEGIN t2\nREAD t2 a\nBEGIN t3\nWRITE t3 a 2\nCOMMIT t3\nWRITE t2 b 2\nCOMMIT t2\nBEGIN t4\nREAD t4 b\nBEGIN t5\nWRITE t5 b 3\nCOMMIT t4\nCOMMIT t5\nCHECKPOINT\n",
        "a=2\nb=3\nCHECKPOINT:\na=2\nb=3\nCONFLICTS:\nt2\n",
    ),
}


@pytest.mark.parametrize("name", list(CASES.keys()))
def test_txlog(name):
    ops, expected = CASES[name]
    assert _norm(run_txlog(ops)) == _norm(expected)
