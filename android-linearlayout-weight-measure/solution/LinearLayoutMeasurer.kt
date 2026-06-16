package com.example.layout

class LinearLayoutMeasurer {
    private val children = mutableListOf<Child>()
    private var totalWidth: Int = 0
    private var remaining: Int = 0
    private var overflow: Boolean = false

    fun addChild(id: String, kind: ChildKind, value: Int, margin: Int) {
        children += Child(id, kind, value, margin)
    }

    fun measure(width: Int) {
        totalWidth = width
        val usedWidth = measureNonWeightPass()
        remaining = width - usedWidth
        overflow = remaining < 0
        distributeWeights(maxOf(0, remaining))
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
        if (weighted.size == 1) {
            weighted[0].measured = distributable
            return
        }
        val totalWeight = weighted.sumOf { it.value }
        val complementSum = weighted.sumOf { totalWeight - it.value }
        if (complementSum == 0) {
            weighted.forEach { it.measured = 0 }
            return
        }
        var distributed = 0
        for ((index, child) in weighted.withIndex()) {
            if (index == weighted.lastIndex) {
                child.measured = distributable - distributed
            } else {
                val complement = totalWeight - child.value
                val share = distributable * complement / complementSum
                child.measured = share
                distributed += share
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
            builder.append("measuredWidth=${child.measured} start=${child.start}\n")
        }
    }
}
