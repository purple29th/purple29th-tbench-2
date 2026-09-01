package com.example.recycler

class FetchScheduler(private val pool: RecyclerPool) {
    private val pending = mutableListOf<AsyncFetch>()
    private val resolutions = mutableMapOf<String, ArrayDeque<String>>()
    private var sequenceCounter: Long = 0L

    private var budgeted = false
    private var refillNum = 0L
    private var refillDen = 1L
    private var capUnits = 0L
    private var budgetUnits = 0L
    private var lastNow = 0L

    fun schedule(cellId: String, itemId: String, expectedToken: Long, dueAt: Long) {
        sequenceCounter += 1
        pending.add(AsyncFetch(sequenceCounter, cellId, itemId, expectedToken, dueAt))
    }

    fun queueResolution(itemId: String, imageUrl: String) {
        resolutions.getOrPut(itemId) { ArrayDeque() }.addLast(imageUrl)
    }

    fun setBudget(num: Long, den: Long, cap: Long) {
        budgeted = true
        refillNum = num
        refillDen = den
        capUnits = cap * den
        if (budgetUnits > capUnits) budgetUnits = capUnits
    }

    fun advance(now: Long) {
        if (budgeted) {
            val dt = now - lastNow
            if (dt > 0) budgetUnits += dt * refillNum
            if (budgetUnits > capUnits) budgetUnits = capUnits
        }
        lastNow = now

        val due = pending.filter { it.dueAt <= now }
            .sortedWith(compareBy({ it.dueAt }, { it.sequence }, { it.cellId }))

        val processed = mutableListOf<AsyncFetch>()
        for (fetch in due) {
            val cell = pool.cell(fetch.cellId)
            val valid = cell.bindingToken == fetch.expectedToken
            if (valid && budgeted && budgetUnits < refillDen) {
                break
            }
            val queue = resolutions[fetch.itemId]
            val url = queue?.removeFirstOrNull() ?: "auto:${fetch.itemId}"
            val applied = cell.applyImage(url, fetch.expectedToken)
            if (applied) {
                if (budgeted) budgetUnits -= refillDen
                pool.afterImageApplied(fetch.cellId)
            }
            processed.add(fetch)
        }
        pending.removeAll(processed.toSet())
    }
}
