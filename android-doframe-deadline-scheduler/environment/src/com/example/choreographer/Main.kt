package com.example.choreographer

import java.io.File

private const val DEFAULT_SCENARIO_PATH = "/app/scenario.txt"
private const val DEFAULT_OUTPUT_PATH = "/app/output.txt"

private val REPEAT_BY_LABEL = mapOf("once" to Repeat.ONCE, "repeat" to Repeat.REPEAT)
private val PRIORITY_BY_LABEL = mapOf("sync" to MessagePriority.SYNC, "async" to MessagePriority.ASYNC)

fun main(args: Array<String>) {
    val scenarioPath = args.getOrNull(0) ?: DEFAULT_SCENARIO_PATH
    val outputPath = args.getOrNull(1) ?: DEFAULT_OUTPUT_PATH
    val scheduler = DoFrameScheduler()
    val output = StringBuilder()

    File(scenarioPath).forEachLine { raw ->
        val line = raw.trim()
        if (line.isNotEmpty()) dispatch(line, scheduler, output)
    }

    File(outputPath).writeText(output.toString())
}

private fun dispatch(line: String, scheduler: DoFrameScheduler, output: StringBuilder) {
    val tokens = line.split(" ")
    when (tokens[0]) {
        "SET_VSYNC_RATE"      -> scheduler.setVsyncRate(tokens[1].toInt())
        "POST_FRAME"          -> scheduler.postFrame(tokens[1], Phase.valueOf(tokens[2]), tokens[3].toInt(), repeatOf(tokens[4]))
        "REMOVE_FRAME"        -> scheduler.removeFrame(tokens[1])
        "POST_INPUT"          -> scheduler.postInput(tokens[1].toInt(), tokens[2].toInt(), tokens[3].toInt())
        "POST_MESSAGE"        -> scheduler.postMessage(priorityOf(tokens[1]), tokens[2].toInt())
        "SCHEDULE_TRAVERSALS" -> scheduler.scheduleTraversals()
        "DO_FRAME"            -> scheduler.doFrame(tokens[1].toInt())
        "DRAIN_QUEUE"         -> scheduler.drainQueue(tokens[1].toInt())
        "QUERY"               -> output.append(scheduler.snapshot())
    }
}

private fun repeatOf(label: String): Repeat =
    REPEAT_BY_LABEL[label] ?: error("unknown repeat: $label")

private fun priorityOf(label: String): MessagePriority =
    PRIORITY_BY_LABEL[label] ?: error("unknown priority: $label")
