package com.example.config

class ExposureCache {
    private val seen = mutableSetOf<DedupKey>()

    fun shouldLog(user: String, session: Int, config: String, param: String): Boolean =
        seen.add(DedupKey(user, config, param))

    fun invalidate(user: String, session: Int, config: String) {}

    private data class DedupKey(val a: String, val b: String, val c: String)
}
