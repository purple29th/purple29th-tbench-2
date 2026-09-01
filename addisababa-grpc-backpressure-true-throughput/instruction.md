I am Abebe from Addis Ababa Ethiopia, I work on telemetry for drone delivery startup that flies medicine to villages. We have HTTP2 multiplexer layer that gRPC rides on. Connection window and stream windows start at sixty five five thirty five. DATA frames spend both windows, HEADERS spends none. Reserved floor forty ninety six off limits to DATA per tick. Weighted fair share split by weight with remainder to highest weight lowest id tie break. Stream id parity must be odd client even server, half closed credit updates, CLOSED state rendering.

Bug is throughput miscalc when window updates interleave with floor blocks and when many streams compete, remainder goes to wrong stream, parity check missing, half closed still allows DATA.

We have seven scenarios in environment/scenarios: main, floor_blocks, half_closed_update, parity, rst_stream, adversarial, weight_range. Each scenario file contains frame log and expected throughput file in tests/expected.

Please fix src/main/java/com/example/grpc/StreamMultiplexer.kt and FlowController.kt.

We call run via gradle and tests check expected vs actual output txt.

File layout gprc Android style Kotlin.

If you get weighted fair share plus remainder tie break plus floor plus parity plus half closed right you pass.

Coding rules Kotlin.

Author Tosin Daniel Jimoh purple29th at meta.com


We have seven scenarios in environment/scenarios: main.txt simple two streams weight 50 50, floor_blocks.txt where reserved floor forty ninety six blocks DATA when window low, half_closed_update.txt where stream half closed still needs credit update for WINDOW_UPDATE, parity.txt where client must be odd server even, rst_stream.txt where RST_STREAM closes and frees window, adversarial.txt interleaves many streams with small windows, weight_range.txt weight one to two hundred fifty six edge.

Each scenario file contains lines like STREAM id weight, DATA stream_id size, WINDOW_UPDATE connection delta stream delta, HEADERS, RST_STREAM. Output is frame log interleaved per pass in open order plus final throughput per stream.

Weighted fair share split: each tick total available connection window minus reserved floor split proportionally to stream weight among open streams that still need data. Remainder after integer division goes to highest weight lowest id tie break, that is important for budget_two_thirds style remainder accumulation.

Stream state machine: IDLE, OPEN, HALF_CLOSED_LOCAL, HALF_CLOSED_REMOTE, CLOSED. DATA in CLOSED must be error. WINDOW_UPDATE in HALF_CLOSED_LOCAL still updates connection window but not stream. Parity check: client initiated streams must be odd, server even, otherwise PROTOCOL_ERROR.

Our current StreamMultiplexer.kt has bugs: floor ignored so DATA sent when window below floor, remainder goes to lowest weight not highest, parity not checked, half closed allows DATA.

Fix must handle all.

Files: environment/scenarios seven files, environment/src/com/example/grpc/ StreamMultiplexer.kt, FrameTypes.kt, Main.kt, StreamState.kt, solution/StreamMultiplexer.kt oracle correct, tests/expected seven expected, test_outputs.py runs bash.

Completion Oracle three of three all seven scenarios pass, Avocado zero to one of five due to remainder tie break and floor and parity.

Author Tosin Daniel Jimoh purple29th at meta.com
