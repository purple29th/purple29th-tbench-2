# codimango/transaction-log-replay

## Description

The agent must implement a C++ program (`/app/txlog`) that replays a stream of `BEGIN`, `WRITE`, `SAVEPOINT`, `ROLLBACK_TO`, `COMMIT`, `ABORT`, and `CHECKPOINT` operations from stdin and prints the final committed key/value state followed by the latest checkpoint snapshot. Transactions stage writes privately and can mark intermediate savepoints; `ROLLBACK_TO` rewinds a transaction to a named savepoint without closing it, leaving the savepoint itself intact for further rollbacks. `CHECKPOINT` atomically captures the globally committed state at the moment it runs.

The task tests precise stateful reasoning rather than algorithmic cleverness. The traps are that `ROLLBACK_TO` must undo everything written after the savepoint while keeping the savepoint usable for subsequent rollbacks, that an earlier `CHECKPOINT` does not retroactively include transactions that commit later, that `ABORT` discards every write the transaction made (not just the most recent), that any operation referencing an unknown or already-closed transaction is a silent no-op, and that a closed transaction id cannot be reused via `BEGIN`. Models that drop savepoint state on rollback, allow re-`BEGIN` of closed ids, or share storage between the committed store and snapshots fail subtle test cases.

## Completion Rates

Each run is `k=5` trials. A trial scores `1.0` only if all verification tests pass.

| Model | Pass rate (k=5) |
|---|---|
| Oracle | 3/3 (1.00) deterministic |
| Avocado (`meta/avocado_dvsc_tester`) | measured by platform on submission |
| Opus 4.6 (`claude-opus-4-6`) | measured by platform on submission |

Calibration target: Avocado or Opus passes at least once and fails at least once across 5 trials.

## Model Analysis

Failure modes the task is designed to surface:

1. Savepoint dropped on rollback — implementations that delete the savepoint after `ROLLBACK_TO` runs fail `savepoint_persists_after_rollback` and `rollback_keeps_savepoint_for_reuse`.
2. Rollback semantics by key, not by write order — implementations that try to "undo per-key" instead of trimming the transaction's write log fail `rollback_then_continue` because the second write to the same key cannot be reasoned about per-key.
3. Retroactive checkpoint inclusion — treating `CHECKPOINT` as a marker and commit time as the snapshot point — fails `checkpoint_excludes_late_commit`.
4. Reopened-transaction semantics — allowing `BEGIN <tx>` to revive a closed transaction id — fails `begin_reuse_after_close_blocked` and `write_after_commit_ignored`.
5. Partial-abort semantics — rolling back only the latest write rather than every write the transaction made — fails the abort-side of `interleaved_commit_and_abort_with_savepoints`.
6. Treating `ROLLBACK_TO` against an unknown savepoint as an error rather than a no-op — fails `rollback_to_unknown_savepoint_noop`.

These reflect reasoning gaps about session-buffered isolation, savepoint lifetime, and atomic checkpoints, not task-setup issues. The environment is deterministic (oracle 3/3) and the C++ entrypoint is unambiguous.

## Anti-Cheating Analysis

- Hardcoded outputs: the oracle implements a real simulation. Tests use varied operation sequences whose outputs depend on the exact interleaving of begin / write / savepoint / rollback / commit / abort / checkpoint — a constant program cannot pass.
- Overfitting to visible tests: test inputs and expected outputs live in `tests/test_outputs.py`, mounted at verification time and hidden from the agent. The program must read arbitrary stdin, so special-casing hidden inputs is impossible.
- Modifying test files: tests run from `/tests`, copied in by the harness after the agent finishes. The reward is written by `tests/test.sh`, outside the agent's control.
- Bypassing the intended solution path: the only way to produce correct output across the 12 distinct operation streams is to implement the actual transaction state machine with savepoint-aware rollback and atomic global checkpoints. The Dockerfile ships only a C++ toolchain — no reference implementation, no `tests/`, no expected outputs.
