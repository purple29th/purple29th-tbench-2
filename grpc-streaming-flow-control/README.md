# codimango/grpc-streaming-flow-control

## Description

A Kotlin simulator of an HTTP/2-style stream multiplexer used as gRPC's wire protocol in a service-to-service mesh. One connection multiplexes many concurrent RPC streams; flow control and stream priority govern when each queued DATA frame may emit. The current StreamMultiplexer.kt has multiple bugs across stream-id parity validation, weight-proportional bandwidth allocation, lifecycle state transitions, and credit-replenishment edge cases. The agent must fix StreamMultiplexer.kt so the multiplexer's emitted frame log matches the expected behavior across multi-stream contention, mid-flight resets, and post-half-close window updates.

## Completion Rates

Each run is k=5 trials. A trial scores 1.0 only if /app/output.txt matches expected.txt exactly.

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | 1/5 (0.20) [harder adversarial scenario] |
| Opus 4.6 (claude-opus-4-6)         | 5/5 (1.00) |

## Model Analysis

Failure modes the task is designed to surface — production bug classes from real HTTP/2 multiplexers (gRPC, nghttp2, Netty's HTTP/2 codec):

1. Weight-proportional vs. priority-absolute. A stream with weight 48 vs another with weight 16 must receive 3x the share of the constrained connection window, not 100% of it. Implementations that pattern-match HTTP/2 priority as "highest wins" cause the lower-weight stream to permanently starve under contention.
2. Stream-id parity. Client-initiated streams use odd ids, server-initiated use even, control is id 0. A multiplexer that accepts even ids from the client side accepts protocol-violating frames that real HTTP/2 stacks would reject with PROTOCOL_ERROR.
3. WINDOW_UPDATE on HALF_CLOSED_LOCAL. After a stream sends endStream=true, the sender's half closes but the stream itself is still alive — receivers may still issue WINDOW_UPDATE (e.g., via trailers / late ack) and the sender must apply the credit. Implementations that treat half-close as "no more activity for this stream" silently drop these and break receivers that depend on flow-control round-trips.
4. CLOSED-stream window display. After RST_STREAM, the stream's window credit is conceptually released; a snapshot showing the pre-reset window value misleads operators debugging credit accounting.
5. Connection-window precedence. Even when a per-stream window has credit, emission cannot proceed if the connection window is exhausted. Implementations that gate only on the per-stream window over-send and corrupt receiver-side accounting.

## Anti-Cheating Analysis

- Hardcoded outputs. The scenario interleaves a parity violation, weight-proportional contention with a non-trivial integer-division remainder (16 vs 48 weights against an odd 65535 window producing a 1-byte remainder), a follow-up tick that drains both queues, an end-stream transition with a post-close credit update, and a reset of a separate stream — three QUERY snapshots whose values diverge from the buggy code in every section.
- Modifying test files. Tests run from /tests, copied in by the harness after the agent finishes. The reward is written by tests/test.sh.
- Bypassing the intended solution. The only way to pass is to implement correct stream-id parity, weight-proportional allocation, half-closed window updates, and reset-state rendering in StreamMultiplexer.kt. The Dockerfile ships only JDK + Kotlin compiler; no reference implementation, no expected output.
