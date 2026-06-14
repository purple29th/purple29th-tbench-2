# codimango/android-recycler-staleness

## Description

The agent works in a Kotlin project simulating a RecyclerView-style cell pool. A small set of reusable cells get bound, recycled, and rebound as a user "scrolls"; each binding also schedules an asynchronous image fetch that may resolve later. The current implementation has a stale-callback bug class — async fetches scheduled before a recycle or rebind can write through to the cell after its binding has changed. The agent must fix `RecyclerPool.kt` and `FetchScheduler.kt` so that no fetch ever updates a cell whose binding has changed since the fetch was scheduled.

The task tests precise stateful reasoning across a real production bug pattern, not algorithmic cleverness. The traps are that recycling a cell must invalidate pending fetches (not just clear the displayed state), that rebinding to a *different* item must do the same, that rebinding to the *same* item still invalidates the older fetch (binding identity, not item identity, is what matters), and that resolving multiple fetches in a single `TICK` must check token validity at write time rather than batching naïvely.

## Completion Rates

Each run is `k=5` trials. A trial scores `1.0` only if all 12 verification scenarios pass.

| Model | Pass rate (k=5) |
|---|---|
| Oracle | 3/3 (1.00) deterministic |
| Avocado (`meta/avocado_dvsc_tester`) | measured by platform on submission |
| Opus 4.6 (`claude-opus-4-6`) | measured by platform on submission |

Calibration target: Avocado or Opus passes at least once and fails at least once across 5 trials.

## Model Analysis

Failure modes the task is designed to surface:

1. No token bump on recycle. The cell's binding token is reused, so a previously-scheduled fetch with the same expected token writes through after recycle. Fails `recycle_invalidates_pending`, `rapid_recycle_and_rebind`.
2. No token bump on rebind. Rebinding doesn't invalidate the prior fetch. Fails `rebind_to_different_item`, `interleaved_binds_across_cells`.
3. Item-identity used as token. Implementations that compare by `item_id` (rather than a generation token) miss the case where a cell is rebound to the same item — the fetch from the old binding still carries that item_id and writes through. Fails `rebind_same_item_invalidates_old`.
4. Batched-resolve mistake. Implementations that collect resolutions before applying them allow earlier writes to corrupt cells whose tokens were valid mid-loop but invalid by write time. Fails edge cases on `multiple_pending_resolve_in_order` under specific binding interleavings.

These reflect the exact production-bug class that ships in real Android apps: stale async results writing to recycled or rebound RecyclerView cells.

## Anti-Cheating Analysis

- Hardcoded outputs: scenarios use varied operation sequences whose expected outputs depend on token-correctness across recycle/rebind/tick boundaries. A constant program cannot pass.
- Overfitting to visible tests: visible contract tests cover a subset of behaviors. The hidden verifier scenarios stress edge cases (rapid recycle, interleaved binds across cells, auto-URL fallback, partial tick).
- Modifying test files: tests run from `/tests`, copied in by the harness after the agent finishes. The reward is written by `tests/test.sh`, outside the agent's control.
- Bypassing the intended solution path: the only way to pass all 12 scenarios is to implement correct binding-token invalidation in both `RecyclerPool` and `FetchScheduler`. The Dockerfile ships only JDK + Kotlin compiler — no reference implementation, no `tests/`, no expected outputs.
