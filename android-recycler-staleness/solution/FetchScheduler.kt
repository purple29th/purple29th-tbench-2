package com.example.recycler

class FetchScheduler(private val pool: RecyclerPool) {
    private val pending = mutableListOf<AsyncFetch>()
    private val resolutions = mutableMapOf<String, ArrayDeque<String>>()
    private var sequenceCounter: Long = 0L

    fun schedule(cellId: String, itemId: String, expectedToken: Long, dueAt: Long) {
        sequenceCounter += 1
        pending.add(AsyncFetch(sequenceCounter, cellId, itemId, expectedToken, dueAt))
    }

    fun queueResolution(itemId: String, imageUrl: String) {
        resolutions.getOrPut(itemId) { ArrayDeque() }.addLast(imageUrl)
    }

    fun advance(now: Long) {
        val due = pending.filter { it.dueAt <= now }
            .sortedWith(compareBy({ it.dueAt }, { it.sequence }, { it.cellId }))
        pending.removeAll(due.toSet())

        for (fetch in due) {
            val queue = resolutions[fetch.itemId]
            val url = queue?.removeFirstOrNull() ?: "auto:${fetch.itemId}"
            val applied = pool.cell(fetch.cellId).applyImage(url, fetch.expectedToken)
            if (applied) pool.afterImageApplied(fetch.cellId)
        }
    }
}
