package com.example.bitmappool

private const val MAX_SIZE_BYTES = 32768

class BitmapPool {
    private val strong = mutableMapOf<String, StrongEntry>()
    private val soft = mutableListOf<SoftEntry>()
    private val active = mutableMapOf<String, Int>()
    private val events = mutableListOf<String>()
    private var currentBytes: Int = 0
    private var currentTick: Long = 0

    fun alloc(key: String, width: Int, height: Int, config: BitmapConfig) {
        currentTick += 1
        val spec = BitmapSpec(width, height, config)
        currentBytes += spec.bytes
        strong[key] = StrongEntry(key, spec, currentTick)
        events += "ALLOC $key"
        evictUntilFits()
    }

    fun beginDraw(key: String) {
        currentTick += 1
        if (key !in strong) return
        active[key] = (active[key] ?: 0) + 1
    }

    fun endDraw(key: String) {
        currentTick += 1
        val depth = active[key] ?: return
        if (depth <= 1) active.remove(key) else active[key] = depth - 1
    }

    fun recycle(key: String) {
        currentTick += 1
        val entry = strong[key] ?: return
        val drawDepth = active[key] ?: 0
        if (drawDepth > 0) {
            events += "LEAK $key"
            currentBytes -= entry.spec.bytes
            strong.remove(key)
            active.remove(key)
            return
        }
        val duplicate = strong.values.firstOrNull { it.key != key && sameSpec(it.spec, entry.spec) }
        if (duplicate != null) {
            strong.remove(duplicate.key)
            currentBytes -= duplicate.spec.bytes
            events += "DEDUP ${duplicate.key}"
            soft += SoftEntry(duplicate.key, duplicate.spec, duplicate.lastAccess)
        }
        entry.lastAccess = currentTick
    }

    fun acquire(key: String, width: Int, height: Int, config: BitmapConfig) {
        currentTick += 1
        val spec = BitmapSpec(width, height, config)
        val strongHit = strong.values.firstOrNull { sameSpec(it.spec, spec) }
        if (strongHit != null) {
            val preservedLastAccess = strongHit.lastAccess
            strong.remove(strongHit.key)
            strong[key] = StrongEntry(key, spec, preservedLastAccess)
            events += "REUSE_STRONG $key"
            return
        }
        val softIndex = soft.indexOfFirst { sameSpec(it.spec, spec) }
        if (softIndex >= 0) {
            val softHit = soft.removeAt(softIndex)
            currentBytes += spec.bytes
            strong[key] = StrongEntry(key, spec, softHit.lastAccess)
            events += "REUSE_SOFT $key"
            evictUntilFits()
            return
        }
        currentBytes += spec.bytes
        strong[key] = StrongEntry(key, spec, currentTick)
        events += "ALLOC $key"
        evictUntilFits()
    }

    fun gc() {
        currentTick += 1
        val cleared = soft.size
        soft.clear()
        events += "GC cleared=$cleared"
    }

    fun snapshot(): String = buildString {
        appendPool(this)
        appendStrong(this)
        appendSoft(this)
        appendActive(this)
        appendEvents(this)
    }

    private fun sameSpec(candidate: BitmapSpec, request: BitmapSpec): Boolean =
        candidate.width == request.width &&
            candidate.height == request.height &&
            candidate.config == request.config

    private fun evictUntilFits() {
        while (currentBytes > MAX_SIZE_BYTES) {
            val victim = chooseVictim() ?: return
            val sharedTick = strong.values.count { it.lastAccess == victim.lastAccess } > 1
            strong.remove(victim.key)
            currentBytes -= victim.spec.bytes
            val reason = if (sharedTick) "tie" else "lru"
            events += "EVICT ${victim.key} reason=$reason"
            soft += SoftEntry(victim.key, victim.spec, victim.lastAccess)
        }
    }

    private fun chooseVictim(): StrongEntry? {
        if (strong.isEmpty()) return null
        return strong.values
            .sortedWith(compareBy({ it.lastAccess }, { it.spec.bytes }, { it.key }))
            .first()
    }

    private fun appendPool(builder: StringBuilder) {
        builder.append("pool maxBytes=$MAX_SIZE_BYTES currentBytes=$currentBytes\n")
    }

    private fun appendStrong(builder: StringBuilder) {
        builder.append("strong:\n")
        for (entry in strong.values.sortedBy { it.key }) {
            builder.append("  key=${entry.key} w=${entry.spec.width} h=${entry.spec.height} ")
            builder.append("config=${entry.spec.config} bytes=${entry.spec.bytes} lastAccess=${entry.lastAccess}\n")
        }
    }

    private fun appendSoft(builder: StringBuilder) {
        builder.append("soft:\n")
        for (entry in soft.sortedBy { it.key }) {
            builder.append("  key=${entry.key} w=${entry.spec.width} h=${entry.spec.height} ")
            builder.append("config=${entry.spec.config} bytes=${entry.spec.bytes}\n")
        }
    }

    private fun appendActive(builder: StringBuilder) {
        builder.append("active:\n")
        for ((key, depth) in active.toSortedMap()) {
            builder.append("  key=$key depth=$depth\n")
        }
    }

    private fun appendEvents(builder: StringBuilder) {
        builder.append("events:\n")
        for (event in events) builder.append("  $event\n")
    }
}
