package com.example.inventory

import java.io.File

private const val SCENARIO_PATH = "/app/scenario.txt"
private const val OUTPUT_PATH = "/app/output.txt"

fun main() {
    val inventory = Inventory()
    val store = ReservationStore(inventory)
    val out = StringBuilder()

    File(SCENARIO_PATH).forEachLine { raw ->
        val line = raw.trim()
        if (line.isEmpty()) return@forEachLine
        dispatch(line, inventory, store, out)
    }

    File(OUTPUT_PATH).writeText(out.toString())
}

private fun dispatch(line: String, inventory: Inventory, store: ReservationStore, out: StringBuilder) {
    val tokens = line.split(" ")
    when (tokens[0]) {
        "STOCK"   -> inventory.addStock(tokens[1], tokens[2].toInt())
        "RESERVE" -> store.reserve(tokens[1], tokens[2], tokens[3].toInt(), tokens[4].toLong())
        "COMMIT"  -> store.commit(tokens[1])
        "CANCEL"  -> store.cancel(tokens[1])
        "TICK"    -> store.tick(tokens[1].toLong())
        "QUERY"   -> out.append(inventory.snapshot())
    }
}
