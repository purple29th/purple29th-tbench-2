Fix /app/src/com/example/grpc/StreamMultiplexer.kt, an HTTP/2 multiplexer (gRPC's wire layer) whose frame logs are wrong in a few cases. Change only that file, not Main.kt, FrameTypes.kt, or StreamState.kt. The verifier builds and runs it.

/app/scenario.txt has one op per line. OPEN_STREAM <streamId> <weight> opens a client stream, weight 1 to 256. SEND_HEADERS <streamId> emits a HEADERS frame (bytes=0, no window effect). SEND_DATA <streamId> <bytes> <endStream> queues a DATA frame; emitting it spends the stream and connection windows, and endStream=true half-closes the stream once its bytes drain. WINDOW_UPDATE <streamId|0> <inc> credits a stream window (id nonzero) or the connection window (id 0). RST_STREAM <streamId> drops the stream's queued data, releases its window credit, and the snapshot then shows window=0. ACK_BYTES <streamId> <bytes> returns that many already-sent bytes to the connection window. HALF_CLOSE_LOCAL <streamId> stops new DATA but still accepts WINDOW_UPDATE. TICK drains queued DATA under flow control and priority. QUERY appends a snapshot to /app/output.txt.

The shared connection window and each stream's own window both start at 65535. DATA emission subtracts from both; HEADERS from neither. The connection window refills from WINDOW_UPDATE on id 0 or any ACK_BYTES; a stream window refills from WINDOW_UPDATE on its id. A reserved floor of 4096 is off-limits to DATA, so each TICK hands out at most (connectionWindow minus 4096) bytes total, and zero once the window is at or below 4096. Real emission still subtracts normally; the floor is a per-tick cap, not a counter.

Clients use odd ids, servers even, and id 0 is the control stream (WINDOW_UPDATE only). A stream goes IDLE, OPEN, optionally HALF_CLOSED_LOCAL, then CLOSED, or straight OPEN to CLOSED on RST_STREAM. It half-closes when an endStream DATA fully drains or immediately on HALF_CLOSE_LOCAL, and still applies WINDOW_UPDATE credit while half-closed. Ops on a CLOSED or unopened stream, or that break parity, exceed the weight range, or misuse id 0, are silently ignored.

On a TICK, if the contending streams' queued bytes exceed the available connection window, split that window by weight. A stream contends if it is OPEN or HALF_CLOSED_LOCAL with queued DATA and stream-window credit left. Each gets the smallest of its queued bytes, its stream-window credit, and floor(availableConnectionWindow * streamWeight / sumOfContendingWeights). The integer-division remainder goes to the highest-weight contender, ties to the lowest id. Repeat the drain within the TICK until nobody can progress (no queue, no stream credit, or no connection credit). A TICK's DATA frames are logged in the order their streams were opened.

Each QUERY appends:
  connection window=<n>
  streams:
    id=<n> state=<STATE> weight=<w> window=<n> queued=<n> sent=<n>
  frames:
    <TYPE> stream=<n> bytes=<n>
streams lists every opened stream sorted by id; a closed one stays CLOSED with queued 0, window 0, and sent equal to the bytes it emitted before closing. frames is the cumulative emission log: HEADERS with bytes=0, DATA with bytes actually sent, rejected ops nothing.

Debug only, from /app: kotlinc src/com/example/grpc/*.kt -include-runtime -d /app/sim.jar then java -jar /app/sim.jar; it reads /app/scenario.txt and writes /app/output.txt.
