# codimango/lru-cache-with-cost-budget

## Description

The agent must implement a C++ program (`/app/cache`) that simulates a memory-budgeted cache processing `PUT`, `GET`, `EVICT_TO`, and `TICK` operations from stdin and prints surviving entries in least-recently-used-first order to stdout. Eviction is recency-driven with a cost-aware tie-breaker, and the budget is an at-most bound rather than a strict ceiling.

The task tests precise stateful reasoning rather than algorithmic cleverness. The traps are that eviction is LRU first but within a recency tier the higher-cost entry leaves first, that `EVICT_TO X` is "at most X" not "strictly less than X", and that `PUT` on an existing key is an update — single entry, promoted to MRU, with replaced cost. Models that pick pure LRU, pure cost-greedy, or treat re-PUT as append fail subtle test cases that working implementations handle.

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

1. Pure LRU eviction (ignore cost). Models that reach for textbook LRU and don't apply the cost tie-breaker fail `evict_cost_tie_breaks_lru` — given two same-tier entries with costs 10 and 30 and a budget of 20, they evict the older instead of the costlier.
2. Pure cost-greedy eviction (ignore recency). Models that interpret "memory budget" as "drop biggest things first" fail `evict_recency_dominates_cost` — they evict the cheap-but-newer entry instead of the expensive-but-older one.
3. Strict-less-than budget interpretation. Models that interpret `EVICT_TO X` as "total cost < X" fail `evict_to_exact_budget` by evicting unnecessarily when total cost exactly equals the budget.
4. Re-PUT as append, not update. Models that store entries as a list keyed by insertion fail `put_overwrites_not_appends` because they leave a stale duplicate of the key.
5. Insertion-order output without recency tracking. Models that dump from `std::unordered_map` iteration fail `get_promotes` and `put_promotes_to_mru` because the output ordering itself is part of the contract.

These reflect reasoning gaps about the interaction between recency and cost in memory-budgeted caches, not task-setup issues. The environment is deterministic (oracle 3/3) and the C++ entrypoint is unambiguous.

## Anti-Cheating Analysis

- Hardcoded outputs: The oracle (`solution/cache.cpp`) implements a real simulation. Tests use varied operation sequences whose outputs depend on cost-recency interaction, at-most-budget edge cases, and PUT-update semantics — a constant program cannot pass.
- Overfitting to visible tests: Test inputs and expected outputs live in `tests/test_outputs.py`, mounted at verification time and hidden from the agent. The program must read arbitrary stdin, so special-casing hidden inputs is impossible.
- Modifying test files: Tests run from `/tests`, copied in by the harness after the agent finishes. The reward is written by `tests/test.sh`, outside the agent's control.
- Bypassing the intended solution path: The only way to produce correct output across the 12 distinct operation streams is to implement the actual cost-aware LRU eviction simulation. The Dockerfile ships only a C++ toolchain — no reference implementation, no `tests/`, no expected outputs.
