package com.example.inventory

class Inventory {
    private val rows = mutableMapOf<String, Row>()

    fun addStock(sku: String, qty: Int) {
        rowFor(sku).available += qty
    }

    fun tryReserve(sku: String, qty: Int): Boolean {
        val row = rowFor(sku)
        if (row.available < qty) return false
        row.available -= qty
        row.reserved += qty
        return true
    }

    fun release(sku: String, qty: Int) {
        val row = rows[sku] ?: return
        row.reserved -= qty
        row.available += qty
    }

    fun finalize(sku: String, qty: Int) {
        val row = rows[sku] ?: return
        row.reserved -= qty
        row.sold += qty
    }

    fun snapshot(): String = buildString {
        append("inventory:\n")
        for (sku in rows.keys.sorted()) {
            val row = rows.getValue(sku)
            append("  sku=$sku available=${row.available} reserved=${row.reserved} sold=${row.sold}\n")
        }
    }

    private fun rowFor(sku: String): Row = rows.getOrPut(sku) { Row() }

    private class Row(var available: Int = 0, var reserved: Int = 0, var sold: Int = 0)
}
