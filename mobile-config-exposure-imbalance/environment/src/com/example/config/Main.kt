package com.example.config

import java.io.File

fun main() {
    val sessions = SessionTracker()
    val cache = ExposureCache()
    val mc = MobileConfig(sessions, cache)
    val out = StringBuilder()

    File("/app/scenario.txt").forEachLine { raw ->
        val line = raw.trim()
        if (line.isEmpty()) return@forEachLine
        val p = line.split(" ")
        when (p[0]) {
            "SESSION_START" -> sessions.start(p[1])
            "SESSION_END"   -> sessions.end(p[1])
            "READ"          -> mc.read(p[1], p[2], p[3], p[4])
            "DEFAULT_READ"  -> mc.defaultRead(p[1], p[2], p[3])
            "VARIANT_FLIP"  -> mc.variantFlip(p[1], p[2], p[3])
            "OVERRIDE"      -> mc.override(p[1], p[2], p[3])
            "GRANT"         -> mc.grant(p[1].toLong())
            "PRIORITY"      -> mc.priority(p[1], p[2].toInt())
            "FLUSH"         -> mc.flush()
            "QUERY"         -> out.append(mc.snapshot())
        }
    }
    File("/app/output.txt").writeText(out.toString())
}
