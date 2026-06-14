package com.example.cfgpush

import java.io.File

private const val SCENARIO_PATH = "/app/scenario.txt"
private const val OUTPUT_PATH = "/app/output.txt"

fun main() {
    val store = ConfigStore()
    val out = StringBuilder()
    File(SCENARIO_PATH).forEachLine { raw ->
        val line = raw.trim()
        if (line.isNotEmpty()) dispatch(line, store, out)
    }
    File(OUTPUT_PATH).writeText(out.toString())
}

private fun dispatch(line: String, store: ConfigStore, out: StringBuilder) {
    val t = line.split(" ")
    when (t[0]) {
        "PUSH"               -> store.push(t[1].toLong(), parseUpdates(t[2]))
        "READ"               -> store.read(t[1], t[2])
        "BEGIN_SNAPSHOT"     -> store.beginSnapshot(t[1])
        "READ_FROM_SNAPSHOT" -> store.readFromSnapshot(t[1], t[2])
        "END_SNAPSHOT"       -> store.endSnapshot(t[1])
        "SUBSCRIBE"          -> store.subscribe(t[1], t[2].split(",").toSet())
        "UNSUBSCRIBE"        -> store.unsubscribe(t[1])
        "QUERY"              -> out.append(store.render())
    }
}

private fun parseUpdates(field: String): Map<String, String> =
    field.split(",").associate { pair ->
        val (key, value) = pair.split("=")
        key to value
    }
