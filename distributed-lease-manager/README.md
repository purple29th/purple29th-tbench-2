# codimango/distributed-lease-manager

## Description

A Kotlin simulator of a distributed lease manager with monotonic fencing tokens. Clients acquire/renew/release/transfer leases on named resources; a TICK operation advances time and frees expired leases. The current implementation in LeaseManager.kt has multiple bugs in the lease state machine and the fencing-token lifecycle. The agent must fix LeaseManager.kt so the simulator's output matches the expected log across acquire-on-expired, transfer, renew, and tick-boundary scenarios.

## Completion Rates

Each run is k=5 trials. A trial scores 1.0 only if /app/output.txt matches expected.txt exactly.

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

Failure modes the task is designed to surface — these are real distributed-systems lease semantics that pattern-matching on naïve "lock" abstractions misses:

1. **Fencing-token semantics on RENEW.** Renewal extends the existing lease — same lease, new deadline. The fencing token must NOT advance, because consumers of the protected resource still treat the same lease as a single epoch. Implementations that bump on every state change overshoot fencing on every renewal and break stale-write detection downstream.
2. **Fencing-token persistence on RELEASE.** The fencing token is monotonic per-resource for the lifetime of the simulator; release frees the resource but doesn't reset the counter. Implementations that "reset on release" let the next holder collide with a stale holder's fencing window.
3. **TRANSFER preserves fencing AND deadline.** A transfer hands the *same* lease to a new client — nothing about the lease changes except the holder. Implementations that bump fencing on transfer (treating it as a fresh acquire) corrupt the stale-write fence.
4. **ACQUIRE on an expired lease is one operation, not two.** When ACQUIRE finds the current holder's lease has expired, it should atomically take over: the fencing token advances exactly once. Implementations that "first free, then acquire" double-bump fencing.
5. **Tick-boundary inclusivity.** A lease at exactly deadline=now_ms is expired (≤, not <). The same boundary applies to RENEW/RELEASE/TRANSFER ownership checks: if deadline == now_ms, the lease is no longer valid and the operation must fail.

The traps reflect production bugs in real lease/lock managers (etcd, ZooKeeper-style locks, DynamoDB conditional writes). Models that have read the right systems papers tend to get them; models pattern-matching on a generic "mutex" abstraction tend to miss several.

## Anti-Cheating Analysis

- **Hardcoded outputs:** the scenario sequences acquire / renew / tick-boundary / release / acquire-on-expired / transfer / renew / tick-expire across two resources, with 11 QUERY snapshots whose values depend on getting all five trap behaviors right. A constant program cannot pass.
- **Modifying test files:** tests run from /tests, copied in by the harness after the agent finishes. The reward is written by tests/test.sh.
- **Bypassing the intended solution:** the only way to pass is to implement correct lease-state-machine and fencing-token logic in LeaseManager.kt. The Dockerfile ships only JDK + Kotlin compiler — no reference implementation, no expected output.
