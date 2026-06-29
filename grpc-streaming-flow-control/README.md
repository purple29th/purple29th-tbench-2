# codimango/grpc-streaming-flow-control

## Description

A Kotlin simulator of an HTTP/2-style stream multiplexer used as gRPC's wire protocol in a service-to-service mesh. One connection multiplexes many concurrent RPC streams; flow control and stream priority govern when each queued DATA frame may emit. The current StreamMultiplexer.kt has multiple bugs across stream-id parity validation, weight-proportional bandwidth allocation, lifecycle state transitions, and credit-replenishment edge cases. The agent must fix StreamMultiplexer.kt so the multiplexer's emitted frame log matches the expected behavior across multi-stream contention, mid-flight resets, and post-half-close window updates.

## Completion Rates

Each run is k=5 trials. A trial scores 1.0 only if /app/output.txt matches expected.txt exactly.

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | 1/5 (0.20) [harder adversarial scenario] |
| Opus 4.6 (claude-opus-4-6)         | 2/5 (0.40) |

## Model Analysis

The task is a multi-bug fix across the multiplexer's flow-control, stream-lifecycle, and priority logic. Specific defects are intentionally not enumerated here so the agent must diagnose them from the behavioral spec and the byte-exact expected outputs. Empirical pass rates are in the Completion Rates table above.

## Anti-Cheating Analysis

- Hardcoded outputs. The scenario interleaves a parity violation, weight-proportional contention with a non-trivial integer-division remainder (16 vs 48 weights against an odd 65535 window producing a 1-byte remainder), a follow-up tick that drains both queues, an end-stream transition with a post-close credit update, and a reset of a separate stream — three QUERY snapshots whose values diverge from the buggy code in every section.
- Modifying test files. Tests run from /tests, copied in by the harness after the agent finishes. The reward is written by tests/test.sh.
- Bypassing the intended solution. The only way to pass is to implement correct stream-id parity, weight-proportional allocation, half-closed window updates, and reset-state rendering in StreamMultiplexer.kt. The Dockerfile ships only JDK + Kotlin compiler; no reference implementation, no expected output.
