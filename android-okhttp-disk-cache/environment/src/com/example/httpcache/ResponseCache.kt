package com.example.httpcache

private const val DISK_BUDGET_BYTES = 300000

class ResponseCache {
    private val memory = mutableMapOf<String, MemEntry>()
    private val disk = mutableListOf<DiskEntry>()
    private val inflight = mutableMapOf<String, Int>()
    private val events = mutableListOf<String>()
    private var currentBytes: Int = 0
    private var currentTick: Long = 0

    fun store(key: String, url: String, vary: String, bytes: Int) {
        currentTick += 1
        val spec = ResponseSpec(url, vary, bytes)
        currentBytes += spec.bytes
        memory[key] = MemEntry(key, spec, currentTick)
        events += "STORE $key"
        evictUntilFits()
    }

    fun open(key: String) {
        currentTick += 1
        if (key !in memory) return
        inflight[key] = (inflight[key] ?: 0) + 1
    }

    fun close(key: String) {
        currentTick += 1
        val depth = inflight[key] ?: return
        if (depth <= 1) inflight.remove(key) else inflight[key] = depth - 1
    }

    fun commit(key: String) {
        currentTick += 1
        val entry = memory[key] ?: return
        val depth = inflight[key] ?: 0
        if (depth > 0) {
            events += "ABORT $key"
            currentBytes -= entry.spec.bytes
            memory.remove(key)
            return
        }
        entry.lastAccess = currentTick
    }

    fun lookup(key: String, url: String, vary: String, bytes: Int) {
        currentTick += 1
        val spec = ResponseSpec(url, vary, bytes)
        val memHit = memory.values.firstOrNull { matches(it.spec, spec) }
        if (memHit != null) {
            memory.remove(memHit.key)
            memory[key] = MemEntry(key, spec, currentTick)
            events += "REUSE_MEM $key"
            return
        }
        val diskIndex = disk.indexOfFirst { matches(it.spec, spec) }
        if (diskIndex >= 0) {
            disk.removeAt(diskIndex)
            currentBytes += spec.bytes
            memory[key] = MemEntry(key, spec, currentTick)
            events += "REUSE_DISK $key"
            evictUntilFits()
            return
        }
        currentBytes += spec.bytes
        memory[key] = MemEntry(key, spec, currentTick)
        events += "STORE $key"
        evictUntilFits()
    }

    fun touch(keys: List<String>) {
        currentTick += 1
        val first = keys.firstOrNull() ?: return
        val entry = memory[first] ?: return
        entry.lastAccess = currentTick
    }

    fun trim() {
        currentTick += 1
        val cleared = disk.size
        disk.clear()
        events += "TRIM cleared=$cleared"
    }

    fun snapshot(): String = buildString {
        appendHeader(this)
        appendMemory(this)
        appendDisk(this)
        appendInflight(this)
        appendEvents(this)
    }

    private fun matches(candidate: ResponseSpec, request: ResponseSpec): Boolean {
        return candidate.url == request.url
    }

    private fun evictUntilFits() {
        while (currentBytes > DISK_BUDGET_BYTES) {
            val victim = chooseVictim() ?: return
            memory.remove(victim.key)
            currentBytes -= victim.spec.bytes
            events += "EVICT ${victim.key} reason=lru"
            disk += DiskEntry(victim.key, victim.spec, victim.lastAccess)
        }
    }

    private fun chooseVictim(): MemEntry? {
        if (memory.isEmpty()) return null
        return memory.values.minByOrNull { it.lastAccess }
    }

    private fun appendHeader(builder: StringBuilder) {
        builder.append("cache budget=$DISK_BUDGET_BYTES currentBytes=$currentBytes\n")
    }

    private fun appendMemory(builder: StringBuilder) {
        builder.append("memory:\n")
        for (entry in memory.values.sortedBy { it.key }) {
            builder.append("  key=${entry.key} url=${entry.spec.url} vary=${entry.spec.vary} ")
            builder.append("bytes=${entry.spec.bytes} lastAccess=${entry.lastAccess}\n")
        }
    }

    private fun appendDisk(builder: StringBuilder) {
        builder.append("disk:\n")
        for (entry in disk.sortedBy { it.key }) {
            builder.append("  key=${entry.key} url=${entry.spec.url} vary=${entry.spec.vary} ")
            builder.append("bytes=${entry.spec.bytes}\n")
        }
    }

    private fun appendInflight(builder: StringBuilder) {
        builder.append("inflight:\n")
        for ((key, depth) in inflight.toSortedMap()) {
            builder.append("  key=$key depth=$depth\n")
        }
    }

    private fun appendEvents(builder: StringBuilder) {
        builder.append("events:\n")
        for (event in events) builder.append("  $event\n")
    }
}
