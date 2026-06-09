# codimango/transaction-log-replay

## Description

The agent must implement a C++ program (`/app/txlog`) that replays a stream of `BEGIN`, `WRITE`, `COMMIT`, `ABORT`, and `CHECKPOINT` operations from stdin and prints the final committed key/value state followed by the latest checkpoint snapshot. The store implements snapshot-style isolation: writes are private to their transaction until commit, abort discards them entirely, and checkpoint atomically captures the globally-committed state at the moment it runs.

The task tests precise stateful reasoning rather than algorithmic cleverness. The traps are that a `CHECKPOINT` does NOT retroactively include transactions that commit later, that the latest commit wins on conflicting keys, that `ABORT` discards every write the transaction made (not just the most recent), and that any operation against an already-closed transaction is a silent no-op. Models that conflate "checkpoint = snapshot of all writes so far" or treat closed transactions as still mutable fail subtle test cases.

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

1. Checkpoint as "snapshot of all writes so far" rather than "committed-only at this moment". Models build a write log and dump it at CHECKPOINT, including uncommitted writes — fails `uncommitted_invisible_to_checkpoint`.
2. Retroactive checkpoint inclusion. Models that treat checkpoint as a marker and commit-time as the snapshot point — fails `checkpoint_excludes_late_commit`.
3. Partial-abort semantics. Models that only roll back the latest write rather than every write the transaction made — fails `abort_after_multiple_writes_total`.
4. Reopened-transaction semantics. Models that allow WRITE / COMMIT / ABORT against a closed transaction id — fails `write_after_commit_ignored` and `double_commit_is_noop`.
5. Naive merge on conflicting keys. Models that merge or combine values across committed transactions instead of letting the latest commit overwrite — fails `latest_commit_wins`.

These reflect reasoning gaps about transactional isolation and atomic checkpoints, not task-setup issues. The environment is deterministic (oracle 3/3) and the C++ entrypoint is unambiguous.

## Anti-Cheating Analysis

- Hardcoded outputs: the oracle (`solution/txlog.cpp`) implements a real simulation. Tests use varied operation sequences whose outputs depend on the exact interleaving of begin/commit/abort/checkpoint — a constant program cannot pass.
- Overfitting to visible tests: test inputs and expected outputs live in `tests/test_outputs.py`, mounted at verification time and hidden from the agent. The program must read arbitrary stdin, so special-casing hidden inputs is impossible.
- Modifying test files: tests run from `/tests`, copied in by the harness after the agent finishes. The reward is written by `tests/test.sh`, outside the agent's control.
- Bypassing the intended solution path: the only way to produce correct output across the 12 distinct operation streams is to implement the actual transaction state machine with atomic checkpoints. The Dockerfile ships only a C++ toolchain — no reference implementation, no `tests/`, no expected outputs.
