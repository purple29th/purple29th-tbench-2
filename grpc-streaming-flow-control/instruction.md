# Setting

A simulator of an HTTP/2 multiplexer used as the wire protocol for gRPC in a service-to-service mesh. A single connection carries many concurrent RPC streams; flow control and stream priority prevent any one stream from starving the others or the connection itself.

The current implementation in /app/src/com/example/grpc/StreamMultiplexer.kt produces wrong frame logs across several scenarios. Fix it.

# Operations (/app/scenario.txt)

The driver reads one operation per line.

- OPEN_STREAM <streamId> <weight> — open a client stream. Sets weight in range 1..256.
- SEND_HEADERS <streamId> — emit a HEADERS frame for the stream. Renders with bytes=0. No window impact.
- SEND_DATA <streamId> <bytes> <endStream> — queue a DATA frame on the stream. On emission, consumes both stream and connection windows. If endStream=true, the stream transitions to HALF_CLOSED_LOCAL after the queued bytes drain.
- WINDOW_UPDATE <streamId|0> <increment> — add credit to a stream window (id != 0) or to the connection window (id == 0).
- RST_STREAM <streamId> — abort the stream. Queued data is dropped. The stream's remaining stream-window credit is released (the snapshot shows window=0 after reset).
- ACK_BYTES <streamId> <bytes> — acknowledge that <bytes> of previously-sent data on this stream have been consumed by the receiver. Replenishes the connection window by that amount.
- HALF_CLOSE_LOCAL <streamId> — the sender locally half-closes; no further DATA frames will be queued. The stream may still receive WINDOW_UPDATE from the receiver.
- TICK — drain queued DATA across all streams subject to flow control and priority.
- QUERY — append a snapshot of the multiplexer state to /app/output.txt.

# Flow control

Two windows govern emission:

- Connection window. Shared by all streams. Initial value 65535. Decremented by emitted DATA bytes. Replenished by WINDOW_UPDATE on stream id 0 or by ACK_BYTES on any stream.
- Per-stream window. One per open stream. Initial value 65535. Decremented by emitted DATA bytes on that stream. Replenished by WINDOW_UPDATE on that stream id.

A DATA frame consumes both windows on emission. A HEADERS frame consumes neither.

The connection window has a reserved floor of 4096 bytes that the multiplexer holds back from DATA emission. Each TICK may allocate at most `(connectionWindow - 4096)` bytes total across all contending streams, clamped to zero if the connection window has dropped at or below the floor. Emitted bytes still decrement the actual connection window normally; the floor is a per-tick allocation cap, not a separate counter.

# Stream lifecycle

Stream ids carry parity:

- Client-initiated streams use odd ids.
- Server-initiated streams use even ids.
- Stream id 0 is the control stream and accepts only WINDOW_UPDATE.

State machine:

- IDLE -> OPEN -> HALF_CLOSED_LOCAL -> CLOSED
- IDLE -> OPEN -> CLOSED via RST_STREAM

A stream enters HALF_CLOSED_LOCAL once a SEND_DATA with endStream=true has fully drained from the queue, or immediately on HALF_CLOSE_LOCAL. A stream in HALF_CLOSED_LOCAL may still receive WINDOW_UPDATE and the credit must be applied even though no further DATA will be sent.

Operations targeting a CLOSED stream or a stream that was never opened are dropped silently. The same applies to operations that violate stream-id parity, exceed the weight range, or use a control-stream id where it isn't accepted.

# Priority

Each TICK drains queued DATA. When the total queued bytes across contending streams exceed the available connection window, the available connection window is divided across contending streams proportionally to their weights.

A stream contends in a tick if it is OPEN or HALF_CLOSED_LOCAL, has queued DATA, and has stream-window credit remaining.

For each contending stream, the bytes allocated to it this tick are at most:

- the stream's queued bytes, and
- the stream's remaining stream-window credit, and
- its proportional share of the available connection window, computed as floor(availableConnectionWindow * streamWeight / sumOfWeightsOfContendingStreams).

After the proportional pass, any remainder bytes from integer division go to the contending stream with the highest weight. Ties on weight break by lowest stream id.

The drain repeats within a single TICK until no contending stream can make further progress (no queue, no stream-window credit, or no connection-window credit).

Within a single TICK, the resulting DATA frames are appended to the frames log in the order their streams were opened (the order OPEN_STREAM was issued).

# Output format

Each QUERY appends a snapshot:

  connection window=<n>
  streams:
    id=<n> state=<STATE> weight=<w> window=<n> queued=<n> sent=<n>
    ...
  frames:
    <TYPE> stream=<n> bytes=<n>
    ...

The streams: section lists every stream that has ever been opened, sorted by id ascending. Closed streams are still listed; their state is CLOSED, queued is 0, window is 0, and sent reflects the cumulative bytes emitted before close. The frames: section is the cumulative log of every frame the multiplexer has successfully emitted across the run, in emission order.

HEADERS frames render with bytes=0. DATA frames render with the byte count actually emitted. Rejected operations produce no frame and no log line.

# What you need to do

Fix /app/src/com/example/grpc/StreamMultiplexer.kt. Do not modify Main.kt, FrameTypes.kt, or StreamState.kt. The verifier compiles and runs your fixed code automatically.

# Reference build (local debugging only)

  cd /app
  kotlinc src/com/example/grpc/*.kt -include-runtime -d /app/sim.jar
  java -jar /app/sim.jar

The driver reads /app/scenario.txt and writes /app/output.txt.
