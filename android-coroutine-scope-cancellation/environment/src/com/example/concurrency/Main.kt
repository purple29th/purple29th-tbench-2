package com.example.concurrency

import java.io.File

private const val DEFAULT_SCENARIO_PATH = "/app/scenario.txt"
private const val DEFAULT_OUTPUT_PATH = "/app/output.txt"

private val TYPE_BY_LABEL = mapOf("normal" to JobType.NORMAL, "supervisor" to JobType.SUPERVISOR)

fun main(args: Array<String>) {
    val scenarioPath = args.getOrNull(0) ?: DEFAULT_SCENARIO_PATH
    val outputPath = args.getOrNull(1) ?: DEFAULT_OUTPUT_PATH
    val scope = StructuredScope()
    val output = StringBuilder()

    File(scenarioPath).forEachLine { raw ->
        val line = raw.trim()
        if (line.isNotEmpty()) dispatch(line, scope, output)
    }

    File(outputPath).writeText(output.toString())
}

private fun dispatch(line: String, scope: StructuredScope, output: StringBuilder) {
    val tokens = line.split(" ")
    when (tokens[0]) {
        "LAUNCH"   -> scope.launch(tokens[1], tokens[2], typeOf(tokens[3]))
        "COMPLETE" -> scope.complete(tokens[1])
        "AWAIT"    -> scope.await(tokens[1])
        "FAIL"     -> scope.fail(tokens[1])
        "CANCEL"   -> scope.cancel(tokens[1])
        "QUERY"    -> output.append(scope.snapshot())
    }
}

private fun typeOf(label: String): JobType =
    TYPE_BY_LABEL[label] ?: error("unknown job type: $label")
