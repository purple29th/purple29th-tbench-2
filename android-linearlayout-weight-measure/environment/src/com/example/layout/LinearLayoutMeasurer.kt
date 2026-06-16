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
        distributeWeights()
        layoutPositions()
    }

    fun snapshot(): String = buildString {
        appendHeader(this)
        appendChildren(this)
    }

    private fun measureNonWeightPass(): Int {
        var used = 0
        for (child in children) {
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

    private fun distributeWeights() {
        val weighted = children.filter { it.kind == ChildKind.WEIGHT }
        if (weighted.isEmpty()) return
        val weightSum = weighted.sumOf { it.value }
        if (weightSum == 0) {
            weighted.forEach { it.measured = 0 }
            return
        }
        for (child in weighted) {
            child.measured = totalWidth * child.value / weightSum
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
