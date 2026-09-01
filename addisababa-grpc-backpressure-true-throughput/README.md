# addisababa grpc backpressure true throughput

## Description

I am Abebe from Addis Ababa Ethiopia telemetry for drone delivery. We have HTTP2 multiplexer layer gRPC rides on. Connection window and stream windows start at 65535. DATA spends both windows HEADERS spends none. Reserved floor 4096 off limits to DATA per tick. Weighted fair share split by weight with remainder to highest weight lowest id tie break. Frame log interleaves per pass in open order.

Bug is throughput miscalc when window updates interleave and floor blocks and parity check and half closed credit.

Please fix src/main/java/com/example/grpc/FlowController.kt you fix StreamMultiplexer.kt.

Hidden tests check weighted fair share with scenarios main floor_blocks half_closed_update parity rst_stream adversarial weight_range.

Files: environment/scenarios seven files, src/com/example/grpc/*.kt, solution/StreamMultiplexer.kt oracle, tests/expected seven expected, test_outputs.py runs.

Completion Oracle three of three all scenarios pass, Avocado zero to one of five due to remainder tie break and floor.

Model Analysis no floor reserve violates 4096, no weighted split remainder to highest weight, no parity stream id check, no half closed credit update.

Anti Cheating varied scenarios.

Tags addisababa grpc backpressure throughput drone telemetry

Author Tosin Daniel Jimoh purple29th at meta.com


## Files

* /app/solve.py you write last token
* /app/data/scene sample
* Dockerfile
* solution/solve.py oracle
* tests/_gen.py generates
* test_outputs.py secure verifier random names

## Completion Rates

Oracle three of three deterministic
Avocado zero to one of five
Opus four of five GPT three of five

## Model Analysis

No background overcounts, fixed cutoff over and under, no speck keeps far dust, no shape keeps round, no halo under, hardcoded offset fails 96/128, hardcoded gain fails 22 percent.

## Anti-Cheating

Varied dims spacing amp bg sig noise seed random temp names so constant fails. Secure runner blocks tests.

## Tags

Tags addisababa grpc backpressure true throughput human story

Author Tosin Daniel Jimoh purple29th at meta.com
