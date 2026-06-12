package com.example.recycler

class RecyclerPool {
    private val cells = mutableMapOf<String, Cell>()
    private var tokenCounter: Long = 0L

    fun cell(id: String): Cell = cells.getOrPut(id) { Cell(id) }

    fun bind(cellId: String, itemId: String, title: String): Long {
        val cell = cell(cellId)
        val newToken = nextToken()
        cell.bind(itemId, title, newToken)
        return newToken
    }

    fun recycle(cellId: String) {
        val cell = cell(cellId)
        cell.recycle(nextToken())
    }

    fun snapshot(cellId: String): String {
        val cell = cell(cellId)
        if (!cell.isBound()) return "$cellId unbound"
        val image = cell.imageUrl ?: "NONE"
        return "$cellId item=${cell.itemId} title=${cell.title} imageUrl=$image"
    }

    private fun nextToken(): Long {
        tokenCounter += 1
        return tokenCounter
    }
}
