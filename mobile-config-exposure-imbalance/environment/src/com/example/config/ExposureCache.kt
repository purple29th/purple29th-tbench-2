package com.example.config

class ExposureCache {
    private val seen = mutableSetOf<DedupKey>()

    // BUG: dedup key is per (user, config, param); should be per (user, session, config).
    fun shouldLog(user: String, session: Int, config: String, param: String): Boolean =
        seen.add(DedupKey(user, config, param))

    // BUG: invalidation is a no-op; variant flip and session change must reset entries.
    fun invalidate(user: String, session: Int, config: String) {}

    private data class DedupKey(val a: String, val b: String, val c: String)
}
