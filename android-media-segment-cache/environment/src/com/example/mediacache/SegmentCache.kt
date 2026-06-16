package com.example.mediacache

private const val MEMORY_BUDGET_BYTES = 300000

class SegmentCache {
    private val memory = mutableMapOf<String, MemEntry>()
    private val disk = mutableListOf<DiskEntry>()
    private val playing = mutableMapOf<String, Int>()
    private val events = mutableListOf<String>()
    private var currentBytes: Int = 0
    private var currentTick: Long = 0

    fun buffer(key: String, track: String, durMs: Int, bitrate: Int) {
        currentTick += 1
        val spec = SegmentSpec(track, durMs, bitrate)
        currentBytes += spec.bytes
        memory[key] = MemEntry(key, spec, currentTick)
        events += "BUFFER $key"
        evictUntilFits()
    }

    fun play(key: String) {
        currentTick += 1
        if (key !in memory) return
        playing[key] = (playing[key] ?: 0) + 1
    }

    fun stop(key: String) {
        currentTick += 1
        val depth = playing[key] ?: return
        if (depth <= 1) playing.remove(key) else playing[key] = depth - 1
    }

    fun release(key: String) {
        currentTick += 1
        val entry = memory[key] ?: return
        val depth = playing[key] ?: 0
        if (depth > 0) {
            events += "STALL $key"
            currentBytes -= entry.spec.bytes
            memory.remove(key)
            return
        }
        entry.lastAccess = currentTick
    }

    fun request(key: String, track: String, durMs: Int, bitrate: Int) {
        currentTick += 1
        val spec = SegmentSpec(track, durMs, bitrate)
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
        events += "BUFFER $key"
        evictUntilFits()
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
        appendPlaying(this)
        appendEvents(this)
    }

    private fun matches(candidate: SegmentSpec, request: SegmentSpec): Boolean {
        if (candidate.track != request.track) return false
        return candidate.durMs == request.durMs
    }

    private fun evictUntilFits() {
        while (currentBytes > MEMORY_BUDGET_BYTES) {
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
        builder.append("cache budget=$MEMORY_BUDGET_BYTES currentBytes=$currentBytes\n")
    }

    private fun appendMemory(builder: StringBuilder) {
        builder.append("memory:\n")
        for (entry in memory.values.sortedBy { it.key }) {
            builder.append("  key=${entry.key} track=${entry.spec.track} dur=${entry.spec.durMs} ")
            builder.append("bitrate=${entry.spec.bitrate} bytes=${entry.spec.bytes} lastAccess=${entry.lastAccess}\n")
        }
    }

    private fun appendDisk(builder: StringBuilder) {
        builder.append("disk:\n")
        for (entry in disk.sortedBy { it.key }) {
            builder.append("  key=${entry.key} track=${entry.spec.track} dur=${entry.spec.durMs} ")
            builder.append("bitrate=${entry.spec.bitrate} bytes=${entry.spec.bytes}\n")
        }
    }

    private fun appendPlaying(builder: StringBuilder) {
        builder.append("playing:\n")
        for ((key, depth) in playing.toSortedMap()) {
            builder.append("  key=$key depth=$depth\n")
        }
    }

    private fun appendEvents(builder: StringBuilder) {
        builder.append("events:\n")
        for (event in events) builder.append("  $event\n")
    }
}
