# codimango/inventory-reservation-leaks

## Description

A Kotlin simulator of a warehouse inventory system with stock, reservations, commits, cancels, and time-based expiry. Operations are read from a scenario file; the simulator tracks per-SKU available/reserved/sold counts as a state machine. The current ReservationStore implementation has four lifecycle bugs that compound to produce wildly incorrect inventory snapshots: reservations that expire don't return stock, double-commits double-count sales, cancels on committed orders refund available stock, and duplicate orderId reservations silently overwrite the prior entry leaving qty leaked in reserved.

The agent fixes ReservationStore.kt so that every state transition respects the lifecycle: PENDING is the only state that accepts commit/cancel, expiry must release stock, and orderId is unique.

## Completion Rates

Each run is k=5 trials. A trial scores 1.0 only if /app/output.txt matches the expected inventory log exactly.

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

Failure modes the task is designed to surface:

1. Expiry-without-release. Implementations that mark a reservation EXPIRED without calling release() leak qty into reserved indefinitely. Every subsequent QUERY shows wrong reserved + available counts.
2. Stateless commit. Implementations that finalize on any orderId lookup, regardless of reservation state, accept a second COMMIT for the same order — qty gets double-deducted from reserved (driving it negative) and double-added to sold.
3. Stateless cancel. Implementations that release on any orderId lookup let CANCEL refund a COMMITTED order's qty back to available, leaving sold inflated and total stock conserved only by a coincidence of negative reserved.
4. Duplicate orderId silently overwrites. Implementations that don't reject re-reservation of an existing orderId orphan the original reservation (its qty stays in reserved with no map entry to ever release it).

These reflect a real production bug class in order-fulfillment systems: lifecycle state machines that "look fine" under happy-path tests but corrupt accounting the moment an operation is replayed, expires, or arrives out-of-order.

## Anti-Cheating Analysis

- Hardcoded outputs: the scenario exercises all four bugs across two SKUs with interleaved reservations, expiries, double-commits, and a duplicate orderId. The eight QUERY snapshots diverge from the buggy implementation in five distinct positions, so a constant program cannot pass.
- Modifying test files: tests run from /tests, copied in by the harness after the agent finishes. The reward is written by tests/test.sh.
- Bypassing the intended solution: the only way to pass is to implement correct state-machine validation in ReservationStore. The Dockerfile ships only JDK + Kotlin compiler — no reference, no expected output.
