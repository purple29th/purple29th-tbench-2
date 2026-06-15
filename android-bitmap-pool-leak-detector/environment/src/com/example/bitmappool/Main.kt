package com.example.bitmappool

import java.io.File

private const val DEFAULT_SCENARIO_PATH = "/app/scenario.txt"
private const val DEFAULT_OUTPUT_PATH = "/app/output.txt"

fun main(args: Array<String>) {
    val scenarioPath = args.getOrNull(0) ?: DEFAULT_SCENARIO_PATH
    val outputPath = args.getOrNull(1) ?: DEFAULT_OUTPUT_PATH

    val pool = BitmapPool()
    val output = StringBuilder()

    File(scenarioPath).forEachLine { raw ->
        val line = raw.trim()
        if (line.isNotEmpty()) dispatch(line, pool, output)
    }

    File(outputPath).writeText(output.toString())
}

private fun dispatch(line: String, pool: BitmapPool, output: StringBuilder) {
    val t = line.split(" ")
    when (t[0]) {
        "ALLOC"      -> pool.alloc(t[1], t[2].toInt(), t[3].toInt(), BitmapConfig.fromString(t[4]))
        "BEGIN_DRAW" -> pool.beginDraw(t[1])
        "END_DRAW"   -> pool.endDraw(t[1])
        "RECYCLE"    -> pool.recycle(t[1])
        "ACQUIRE"    -> pool.acquire(t[1], t[2].toInt(), t[3].toInt(), BitmapConfig.fromString(t[4]))
        "GC"         -> pool.gc()
        "QUERY"      -> output.append(pool.snapshot())
    }
}
