package com.example.grpc

import java.io.File

private const val SCENARIO_PATH = "/app/scenario.txt"
private const val OUTPUT_PATH = "/app/output.txt"

fun main() {
    val multiplexer = StreamMultiplexer()
    val output = StringBuilder()

    File(SCENARIO_PATH).forEachLine { raw ->
        val line = raw.trim()
        if (line.isNotEmpty()) dispatch(line, multiplexer, output)
    }

    File(OUTPUT_PATH).writeText(output.toString())
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
