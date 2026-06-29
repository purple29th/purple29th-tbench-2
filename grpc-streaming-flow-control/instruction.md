This simulates the HTTP/2 multiplexer that gRPC uses on the wire: one connection carries many concurrent RPC streams, and flow control plus stream priority keep any single stream from starving the others or the connection. The implementation in /app/src/com/example/grpc/StreamMultiplexer.kt currently produces wrong frame logs in several scenarios — fix it. Don't modify Main.kt, FrameTypes.kt, or StreamState.kt; the verifier compiles and runs your code.

The driver reads /app/scenario.txt, one operation per line:
- OPEN_STREAM <streamId> <weight> opens a client stream with weight in 1..256.
- SEND_HEADERS <streamId> emits a HEADERS frame (renders bytes=0, no window impact).
- SEND_DATA <streamId> <bytes> <endStream> queues a DATA frame; on emission it consumes both the stream and connection windows, and if endStream is true the stream moves to HALF_CLOSED_LOCAL once the queued bytes drain.
- WINDOW_UPDATE <streamId|0> <increment> adds credit to a stream window (id != 0) or to the connection window (id == 0).
- RST_STREAM <streamId> aborts the stream: queued data is dropped and its remaining stream-window credit is released, so the snapshot shows window=0 after reset.
- ACK_BYTES <streamId> <bytes> acknowledges <bytes> already sent on the stream as consumed, replenishing the connection window by that amount.
- HALF_CLOSE_LOCAL <streamId> half-closes locally: no more DATA is queued, but the stream may still receive WINDOW_UPDATE.
- TICK drains queued DATA across all streams under flow control and priority.
- QUERY appends a state snapshot to /app/output.txt.

Two windows govern emission. The connection window is shared by all streams, starts at 65535, drops by emitted DATA bytes, and is replenished by WINDOW_UPDATE on id 0 or by ACK_BYTES on any stream. Each open stream also has its own window, starting at 65535, dropping by that stream's emitted DATA and replenished by WINDOW_UPDATE on its id. A DATA frame consumes both windows; a HEADERS frame consumes neither. The connection window also has a reserved floor of 4096 bytes held back from DATA: each TICK may allocate at most (connectionWindow - 4096) bytes total across contending streams, clamped to zero once the connection window is at or below the floor. Emitted bytes still decrement the real connection window normally — the floor is a per-tick allocation cap, not a separate counter.

Stream ids carry parity: client-initiated streams are odd, server-initiated are even, and id 0 is the control stream that accepts only WINDOW_UPDATE. A stream goes IDLE -> OPEN -> HALF_CLOSED_LOCAL -> CLOSED, or OPEN -> CLOSED via RST_STREAM. It enters HALF_CLOSED_LOCAL once an endStream DATA fully drains or immediately on HALF_CLOSE_LOCAL, and while half-closed it still applies any WINDOW_UPDATE credit even though no more DATA will be sent. Operations targeting a CLOSED or never-opened stream are dropped silently, as are operations that violate parity, exceed the weight range, or use the control-stream id where it isn't accepted.

On each TICK the multiplexer drains queued DATA. When the total queued bytes across contending streams exceed the available connection window, that window is split across them proportionally to weight. A stream contends if it is OPEN or HALF_CLOSED_LOCAL, has queued DATA, and has stream-window credit left. The bytes it gets this tick are the smallest of its queued bytes, its remaining stream-window credit, and its proportional share, floor(availableConnectionWindow * streamWeight / sumOfContendingWeights). Any remainder from the integer division goes to the contending stream with the highest weight, ties broken by lowest stream id. The drain repeats within the TICK until no contending stream can make progress — no queue, no stream-window credit, or no connection-window credit left. Within a TICK, the resulting DATA frames are appended to the frames log in the order their streams were opened (the order OPEN_STREAM was issued).

Each QUERY appends a snapshot:
  connection window=<n>
  streams:
    id=<n> state=<STATE> weight=<w> window=<n> queued=<n> sent=<n>
    ...
  frames:
    <TYPE> stream=<n> bytes=<n>
    ...
The streams section lists every stream ever opened, sorted by id ascending; closed streams stay listed with state CLOSED, queued 0, window 0, and sent equal to the cumulative bytes emitted before close. The frames section is the cumulative log of every frame successfully emitted, in emission order. HEADERS render with bytes=0, DATA render with the bytes actually emitted, and rejected operations produce no frame and no log line.

For local debugging only, from /app run kotlinc src/com/example/grpc/*.kt -include-runtime -d /app/sim.jar then java -jar /app/sim.jar; the driver reads /app/scenario.txt and writes /app/output.txt.
