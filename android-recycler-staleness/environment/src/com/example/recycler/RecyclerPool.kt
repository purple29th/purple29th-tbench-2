package com.example.recycler

class RecyclerPool {
    private val cells = mutableMapOf<String, Cell>()
    private var tokenCounter: Long = 0L

    fun cell(id: String): Cell = cells.getOrPut(id) { Cell(id) }

    fun bind(cellId: String, itemId: String, title: String): Long {
        val cell = cell(cellId)
        // BUG: token is not bumped on bind, so a fetch scheduled before this
        // bind keeps a matching token and writes through.
        cell.bind(itemId, title, cell.bindingToken)
        return cell.bindingToken
    }

    fun recycle(cellId: String) {
        val cell = cell(cellId)
        // BUG: token is not bumped on recycle either, so a fetch in flight
        // when the cell was last bound still resolves onto the recycled cell.
        cell.recycle(cell.bindingToken)
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
