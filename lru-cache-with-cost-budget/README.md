# codimango/lru-cache-with-cost-budget

## Description

The agent implements a C++ program (`/app/cache`) that simulates a memory-budgeted cache processing `PUT`, `GET`, `PIN`, `UNPIN`, `DECAY`, `EVICT_TO`, and `TICK` operations from stdin, and prints the surviving entries in eviction order to stdout. Eviction is recency-driven (tier first) with a cost-aware tie-breaker, pinned entries are never evicted, the budget is an at-most bound, and `DECAY` reclaims headroom over time as a carried fractional quantity.

The task tests precise stateful reasoning. The traps: eviction and output share one order (older tier first; within a tier higher cost first, then key ascending); `EVICT_TO X` is "at most X", not "strictly less than X"; `PUT` on an existing key is an update (single entry, re-stamped to the current tier); pinned entries are skipped during eviction and the cache may stay over budget if it cannot reach the target without them; and `DECAY <num> <den>` accrues headroom continuously, carrying the fractional remainder across ticks rather than recomputing or flooring per tick.

## Output integrity

Expected outputs in `tests/test_outputs.py` are stored as salted SHA-256 digests of the normalized program output, not as plaintext. A program that reads the test file at verify time therefore cannot recover the expected answers from it. Output comparison normalizes trailing whitespace and trailing newlines, so a correct algorithm cannot be failed for a stray newline.

## Completion Rates

Each run is `k=5` trials. A trial scores `1.0` only if all verification tests pass.

Figures below are from the prior revision (v1.0, pre-fix), retained for reference. This revision adds the PIN/UNPIN and DECAY mechanics and resolves the output-ordering spec gap, so it will be re-measured by the platform on submission.

| Model | Pass rate (k=5), v1.0 |
|---|---|
| Oracle | 3/3 (1.00) deterministic |
| Claude (`claude-opus-4-6`) | 3/5 |
| Codex (`gpt-5.5`) | 1/5 |
| Metacode (`meta/avocado_dvsc_tester`) | 2/5 |

Calibration target: at least one strong model passes at least once and fails at least once across 5 trials.

## Model Analysis

Failure modes the task is designed to surface:

1. Pure LRU eviction (ignore cost). Models that apply textbook LRU without the within-tier cost tie-breaker evict the older entry instead of the costlier same-tier one.

2. Pure cost-greedy eviction (ignore recency). Models that read "memory budget" as "drop biggest first" evict a cheap-but-newer entry instead of the expensive-but-older one.

3. Strict-less-than budget. Models that read `EVICT_TO X` as "total < X" evict unnecessarily when the total already equals X.

4. Re-PUT as append. Models that key by insertion leave a stale duplicate instead of updating in place and re-stamping recency.

5. Output ordering. The output uses the same order as eviction (older tier first; within a tier, higher cost first, then key ascending). A defensible early reading was plain MRU-first; this revision states the ordering explicitly so it is a documented requirement rather than an inferred convention, and removes the previously undocumented per-access tiebreak.

6. Pin semantics. Pinned entries are never evicted and the cache may remain over budget; pinning is not an access and does not change recency. Models that treat pin as a touch, or that force the budget by evicting pinned entries, fail.

7. Decay carried remainder. `DECAY <num> <den>` accrues headroom continuously; the reclaimed amount is the whole-number part of what has accumulated. Implementations that floor `num/den` per tick (dropping the remainder each tick) diverge from the exact carried accumulation.

## Anti-Cheating Analysis

- Hardcoded outputs: outputs depend on cost-recency interaction, at-most-budget edges, pin skipping, and carried-remainder decay across varied operation streams; a constant program cannot pass.

- Verify-time reference leak: expected outputs are stored only as salted SHA-256 digests, so a binary that reads `tests/test_outputs.py` at verify time cannot emit the matching expected output. No plaintext expected values or runnable reference are shipped in the verification set.

- Modifying test files: tests run from `/tests`, mounted by the harness after the agent finishes; the reward is written by `tests/test.sh`, outside the agent's control.

- Bypassing the intended path: the only way to pass across the operation streams is to implement the cost-aware, pinned, decay-adjusted LRU simulation. The Dockerfile ships only a C++ toolchain — no reference implementation, no `tests/`, no expected outputs.
