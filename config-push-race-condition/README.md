# codimango/config-push-race-condition

## Description

A Kotlin simulator of a versioned configuration store with three observer/reader concerns: live reads, captured snapshots, and key-subscribed observers receiving push notifications. Inspired by mobile-config / MetaConfig-style infrastructure where a config push must produce exactly one notification per affected observer per version, snapshot readers must see a stable view across in-flight pushes, and unsubscribed observers must immediately stop receiving traffic.

The current ConfigStore implementation has four bugs that distort every QUERY snapshot. The agent must fix ConfigStore.kt so the simulator's output matches the expected log across pushes, snapshot reads, subscribe/unsubscribe, and reader-version tracking.

## Completion Rates

Each run is k=5 trials. A trial scores 1.0 only if /app/output.txt matches expected.txt exactly.

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

Failure modes the task is designed to surface — production bug classes from real config-push infrastructure:

1. **Per-key vs. per-push notification fan-out.** A push that changes N keys an observer cares about must produce ONE notification entry, not N. Implementations that emit one notification per (observer, changed-key) tuple flood downstream consumers and cause duplicate side-effects in the real world.
2. **Snapshot escape.** READ_FROM_SNAPSHOT must read from the captured snapshot, not the live store. Implementations that fall through to the live map silently produce post-push values for callers who explicitly asked for the pre-push view, breaking transactional reads.
3. **Stale observer after unsubscribe.** UNSUBSCRIBE must fully remove the observer from the dispatch list. Implementations that keep the entry around (even with a flag) leak notifications to callers who explicitly disengaged — the canonical "use-after-unsubscribe" leak in long-lived event buses.
4. **Reader version tracking.** A successful READ must update the reader's observed version. Implementations that omit this leave consumers unable to reason about staleness ("did I read before or after that push?") — silent breakage that doesn't produce wrong values, but breaks downstream invariants like "newer reader version implies newer write".

## Anti-Cheating Analysis

- **Hardcoded outputs:** the scenario sequences all four bug classes across two keys, two observers, two readers, with overlapping/non-overlapping push/subscribe sets and four QUERY snapshots. A constant program cannot pass.
- **Modifying test files:** tests run from /tests, copied in by the harness after the agent finishes. The reward is written by tests/test.sh.
- **Bypassing the intended solution:** the only way to pass is to implement correct push notification, snapshot read, unsubscribe, and reader-version logic in ConfigStore.kt. The Dockerfile ships only JDK + Kotlin compiler — no reference, no expected output.
