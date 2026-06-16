package com.example.layout

class LinearLayoutMeasurer {
    private val children = mutableListOf<Child>()
    private var totalWidth: Int = 0
    private var remaining: Int = 0
    private var overflow: Boolean = false

    fun addChild(id: String, kind: ChildKind, value: Int, margin: Int, minWidth: Int) {
        children += Child(id, kind, value, margin, minWidth)
    }

    fun measure(width: Int) {
        totalWidth = width
        val usedWidth = measureNonWeightPass()
        remaining = width - usedWidth
        overflow = remaining < 0
        distributeWeights(maxOf(0, remaining))
        updateHighWaterMarks()
        layoutPositions()
    }

    fun snapshot(): String = buildString {
        appendHeader(this)
        appendChildren(this)
    }

    private fun measureNonWeightPass(): Int {
        var used = 0
        for (child in children) {
            used += child.margin
            when (child.kind) {
                ChildKind.FIXED, ChildKind.WRAP -> {
                    child.measured = child.value
                    used += child.measured
                }
                ChildKind.WEIGHT -> child.measured = 0
            }
        }
        return used
    }

    private fun distributeWeights(distributable: Int) {
        val weighted = children.filter { it.kind == ChildKind.WEIGHT }
        if (weighted.isEmpty()) return
        val pinned = mutableSetOf<String>()
        while (true) {
            val active = weighted.filter { it.id !in pinned }
            if (active.isEmpty()) break
            val weightSum = active.sumOf { it.value }
            if (weightSum == 0) {
                active.forEach { it.measured = 0 }
                break
            }
            val pinnedTotal = weighted.filter { it.id in pinned }.sumOf { it.measured }
            val avail = distributable - pinnedTotal
            assignShares(active, avail, weightSum)
            val belowMin = active.firstOrNull { it.measured < effectiveMin(it) }
            if (belowMin == null) break
            belowMin.measured = effectiveMin(belowMin)
            pinned += belowMin.id
        }
    }

    private fun assignShares(active: List<Child>, avail: Int, weightSum: Int) {
        var distributed = 0
        for ((index, child) in active.withIndex()) {
            if (index == active.lastIndex) {
                child.measured = avail - distributed
            } else {
                val share = avail * child.value / weightSum
                child.measured = share
                distributed += share
            }
        }
    }

    private fun effectiveMin(child: Child): Int = maxOf(child.minWidth, child.hwm)

    private fun updateHighWaterMarks() {
        for (child in children) {
            if (child.kind == ChildKind.WEIGHT) {
                child.hwm = maxOf(child.hwm, child.measured)
            }
        }
    }

    private fun layoutPositions() {
        var offset = 0
        for (child in children) {
            offset += child.margin
            child.start = offset
            offset += child.measured
        }
    }

    private fun appendHeader(builder: StringBuilder) {
        builder.append("measure totalWidth=$totalWidth remaining=$remaining overflow=$overflow\n")
    }

    private fun appendChildren(builder: StringBuilder) {
        builder.append("children:\n")
        for (child in children) {
            builder.append("  id=${child.id} spec=${child.spec()} margin=${child.margin} ")
            builder.append("minWidth=${child.minWidth} measuredWidth=${child.measured} start=${child.start}\n")
        }
    }
}
