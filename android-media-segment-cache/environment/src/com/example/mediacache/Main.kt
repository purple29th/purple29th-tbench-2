package com.example.mediacache

import java.io.File

private const val DEFAULT_SCENARIO_PATH = "/app/scenario.txt"
private const val DEFAULT_OUTPUT_PATH = "/app/output.txt"

fun main(args: Array<String>) {
    val scenarioPath = args.getOrNull(0) ?: DEFAULT_SCENARIO_PATH
    val outputPath = args.getOrNull(1) ?: DEFAULT_OUTPUT_PATH
    val cache = SegmentCache()
    val output = StringBuilder()

    File(scenarioPath).forEachLine { raw ->
        val line = raw.trim()
        if (line.isNotEmpty()) dispatch(line, cache, output)
    }

    File(outputPath).writeText(output.toString())
}

private fun dispatch(line: String, cache: SegmentCache, output: StringBuilder) {
    val t = line.split(" ")
    when (t[0]) {
        "BUFFER"  -> cache.buffer(t[1], t[2], t[3].toInt(), t[4].toInt())
        "PLAY"    -> cache.play(t[1])
        "STOP"    -> cache.stop(t[1])
        "RELEASE" -> cache.release(t[1])
        "REQUEST" -> cache.request(t[1], t[2], t[3].toInt(), t[4].toInt())
        "TRIM"    -> cache.trim()
        "QUERY"   -> output.append(cache.snapshot())
    }
}
