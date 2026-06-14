package com.example.lease

import java.io.File

private const val SCENARIO_PATH = "/app/scenario.txt"
private const val OUTPUT_PATH = "/app/output.txt"

fun main() {
    val mgr = LeaseManager()
    val out = StringBuilder()

    File(SCENARIO_PATH).forEachLine { raw ->
        val line = raw.trim()
        if (line.isEmpty()) return@forEachLine
        dispatch(line, mgr, out)
    }

    File(OUTPUT_PATH).writeText(out.toString())
}

private fun dispatch(line: String, mgr: LeaseManager, out: StringBuilder) {
    val t = line.split(" ")
    when (t[0]) {
        "ACQUIRE"  -> mgr.acquire(t[1], t[2], t[3].toLong(), t[4].toLong())
        "RENEW"    -> mgr.renew(t[1], t[2], t[3].toLong(), t[4].toLong())
        "RELEASE"  -> mgr.release(t[1], t[2], t[3].toLong())
        "TRANSFER" -> mgr.transfer(t[1], t[2], t[3], t[4].toLong())
        "TICK"     -> mgr.tick(t[1].toLong())
        "QUERY"    -> out.append(mgr.snapshot())
    }
}
