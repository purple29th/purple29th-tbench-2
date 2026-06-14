package com.example.config

class ExposureCache {
    private val seen = mutableSetOf<DedupKey>()

    fun shouldLog(user: String, session: Int, config: String, param: String): Boolean =
        seen.add(DedupKey(user, session, config))

    fun invalidate(user: String, session: Int, config: String) {
        seen.remove(DedupKey(user, session, config))
    }

    private data class DedupKey(val user: String, val session: Int, val config: String)
}
