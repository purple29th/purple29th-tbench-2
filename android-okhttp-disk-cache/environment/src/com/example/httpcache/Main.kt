package com.example.httpcache

import java.io.File

private const val DEFAULT_SCENARIO_PATH = "/app/scenario.txt"
private const val DEFAULT_OUTPUT_PATH = "/app/output.txt"

fun main(args: Array<String>) {
    val scenarioPath = args.getOrNull(0) ?: DEFAULT_SCENARIO_PATH
    val outputPath = args.getOrNull(1) ?: DEFAULT_OUTPUT_PATH
    val cache = ResponseCache()
    val output = StringBuilder()

    File(scenarioPath).forEachLine { raw ->
        val line = raw.trim()
        if (line.isNotEmpty()) dispatch(line, cache, output)
    }

    File(outputPath).writeText(output.toString())
}

private fun dispatch(line: String, cache: ResponseCache, output: StringBuilder) {
    val t = line.split(" ")
    when (t[0]) {
        "STORE"  -> cache.store(t[1], t[2], t[3], t[4].toInt())
        "OPEN"   -> cache.open(t[1])
        "CLOSE"  -> cache.close(t[1])
        "COMMIT" -> cache.commit(t[1])
        "LOOKUP" -> cache.lookup(t[1], t[2], t[3], t[4].toInt())
        "TRIM"   -> cache.trim()
        "QUERY"  -> output.append(cache.snapshot())
    }
}
