I am Abebe from Addis Ababa Ethiopia, telemetry for drone delivery. We have HTTP2 multiplexer layer gRPC rides on. Connection window and stream windows start at 65535. DATA spends both windows HEADERS spends none. Reserved floor 4096 off limits to DATA per tick. Weighted fair share split by weight with remainder to highest weight lowest id tie break. Frame log interleaves per pass in open order.

Bug is throughput miscalc when window updates interleave.

Please fix src/main/java/com/example/grpc/FlowController.kt.

Hidden tests check weighted fair share.

Author Tosin Daniel Jimoh
