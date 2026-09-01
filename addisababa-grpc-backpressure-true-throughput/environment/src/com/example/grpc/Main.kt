package com.example.grpc

import java.io.File

private const val DEFAULT_SCENARIO_PATH = "/app/scenario.txt"
private const val DEFAULT_OUTPUT_PATH = "/app/output.txt"

fun main(args: Array<String>) {
    val scenarioPath = args.getOrNull(0) ?: DEFAULT_SCENARIO_PATH
    val outputPath = args.getOrNull(1) ?: DEFAULT_OUTPUT_PATH

    val multiplexer = StreamMultiplexer()
    val output = StringBuilder()

    File(scenarioPath).forEachLine { raw ->
        val line = raw.trim()
        if (line.isNotEmpty()) dispatch(line, multiplexer, output)
    }

    File(outputPath).writeText(output.toString())
}

private fun dispatch(line: String, multiplexer: StreamMultiplexer, output: StringBuilder) {
    val tokens = line.split(" ")
    when (tokens[0]) {
        "OPEN_STREAM"      -> multiplexer.openStream(tokens[1].toInt(), tokens[2].toInt())
        "SEND_HEADERS"     -> multiplexer.sendHeaders(tokens[1].toInt())
        "SEND_DATA"        -> multiplexer.sendData(tokens[1].toInt(), tokens[2].toInt(), tokens[3].toBoolean())
        "WINDOW_UPDATE"    -> multiplexer.windowUpdate(tokens[1].toInt(), tokens[2].toInt())
        "RST_STREAM"       -> multiplexer.resetStream(tokens[1].toInt())
        "ACK_BYTES"        -> multiplexer.ackBytes(tokens[1].toInt(), tokens[2].toInt())
        "HALF_CLOSE_LOCAL" -> multiplexer.halfCloseLocal(tokens[1].toInt())
        "TICK"             -> multiplexer.tick()
        "QUERY"            -> output.append(multiplexer.snapshot())
    }
}
