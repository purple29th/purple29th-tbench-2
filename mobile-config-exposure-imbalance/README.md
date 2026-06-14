# codimango/mobile-config-exposure-imbalance

## Description

A Kotlin project simulating MetaConfig-style mobile configuration reads and exposure logging across app sessions. A driver consumes a scenario file (SESSION_START, READ, DEFAULT_READ, VARIANT_FLIP, OVERRIDE, QUERY) and writes an ordered exposure log used for experiment analysis. The current implementation has four exposure-imbalance bugs that distort the log.

The agent must fix ExposureCache.kt and MobileConfig.kt so the simulator's output matches the contract: every bucketing decision produces exactly one exposure per (user, session, config), with re-exposure on variant flip, no exposure on DEFAULT_READ, and correct override + variant resolution.

## Completion Rates

Each run is k=3 trials. A trial scores 1.0 only if /app/output.txt matches the expected exposure log exactly.

| Model                              | Pass rate (k=3)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

Failure modes the task is designed to surface:

1. Gate-branch drop. Implementations that treat READ ... gate as "not a real bucketing decision" and skip exposure logging miss every gate read. The spec is explicit: every READ is a bucketing decision regardless of branch.
2. Default-read leakage. Implementations that route DEFAULT_READ through the same emit path as READ produce phantom exposures for users who were never bucketed. DEFAULT_READ must be a no-op.
3. Wrong dedup key. Implementations keying dedup on (user, config, param) collapse different sessions into the same dedup bucket, so the second session's read never re-emits. The correct key is (user, session, config).
4. Stale dedup after variant flip. Implementations that update the variant map but don't invalidate the dedup cache silently drop the next read's exposure, so analysis sees the old variant indefinitely.

## Anti-Cheating Analysis

- Hardcoded outputs: the scenario exercises all four bug classes across multiple sessions, with overrides applied late so the output depends on correct dedup invalidation and variant resolution. A constant program cannot pass.
- Modifying test files: tests run from /tests, copied in by the harness after the agent finishes. The reward is written by tests/test.sh.
- Bypassing the intended solution: the only way to pass is to implement correct exposure-logging in both ExposureCache and MobileConfig. The Dockerfile ships only JDK + Kotlin compiler — no reference, no tests, no expected output.
