package com.example.recycler

class FetchScheduler(private val pool: RecyclerPool) {
    private val pending = mutableListOf<AsyncFetch>()
    private val resolutions = mutableMapOf<String, ArrayDeque<String>>()
    private var sequenceCounter: Long = 0L

    private var budgeted = false
    private var refillNum = 0L
    private var refillDen = 1L
    private var cap = 0L
    private var budget = 0L
    private var lastNow = 0L

    fun schedule(cellId: String, itemId: String, expectedToken: Long, dueAt: Long) {
        sequenceCounter += 1
        pending.add(AsyncFetch(sequenceCounter, cellId, itemId, expectedToken, dueAt))
    }

    fun queueResolution(itemId: String, imageUrl: String) {
        resolutions.getOrPut(itemId) { ArrayDeque() }.addLast(imageUrl)
    }

    fun setBudget(num: Long, den: Long, capCredits: Long) {
        budgeted = true
        refillNum = num
        refillDen = den
        cap = capCredits
        if (budget > cap) budget = cap
    }

    fun advance(now: Long) {
        if (budgeted) {
            val dt = now - lastNow
            if (dt > 0) budget += dt * refillNum / refillDen
            if (budget > cap) budget = cap
        }
        lastNow = now

        val due = pending.filter { it.dueAt <= now }
            .sortedWith(compareBy({ it.dueAt }, { it.sequence }, { it.cellId }))

        val processed = mutableListOf<AsyncFetch>()
        for (fetch in due) {
            val cell = pool.cell(fetch.cellId)
            val valid = cell.bindingToken == fetch.expectedToken
            if (valid && budgeted && budget < 1) {
                break
            }
            val queue = resolutions[fetch.itemId]
            val url = queue?.removeFirstOrNull() ?: "auto:${fetch.itemId}"
            val applied = cell.applyImage(url, fetch.expectedToken)
            if (applied) {
                if (budgeted) budget -= 1
                pool.afterImageApplied(fetch.cellId)
            }
            processed.add(fetch)
        }
        pending.removeAll(processed.toSet())
    }
}
