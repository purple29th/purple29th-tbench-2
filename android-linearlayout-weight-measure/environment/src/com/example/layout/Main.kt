package com.example.layout

import java.io.File

private const val DEFAULT_SCENARIO_PATH = "/app/scenario.txt"
private const val DEFAULT_OUTPUT_PATH = "/app/output.txt"

private val KIND_BY_LABEL = mapOf(
    "FIXED" to ChildKind.FIXED,
    "WRAP" to ChildKind.WRAP,
    "WEIGHT" to ChildKind.WEIGHT,
)

fun main(args: Array<String>) {
    val scenarioPath = args.getOrNull(0) ?: DEFAULT_SCENARIO_PATH
    val outputPath = args.getOrNull(1) ?: DEFAULT_OUTPUT_PATH
    val layout = LinearLayoutMeasurer()
    val output = StringBuilder()

    File(scenarioPath).forEachLine { raw ->
        val line = raw.trim()
        if (line.isNotEmpty()) dispatch(line, layout, output)
    }

    File(outputPath).writeText(output.toString())
}

private fun dispatch(line: String, layout: LinearLayoutMeasurer, output: StringBuilder) {
    val t = line.split(" ")
    when (t[0]) {
        "CHILD"   -> layout.addChild(t[1], kindOf(t[2]), t[3].toInt(), t[4].toInt())
        "MEASURE" -> layout.measure(t[1].toInt())
        "QUERY"   -> output.append(layout.snapshot())
    }
}

private fun kindOf(label: String): ChildKind =
    KIND_BY_LABEL[label] ?: error("unknown child kind: $label")
