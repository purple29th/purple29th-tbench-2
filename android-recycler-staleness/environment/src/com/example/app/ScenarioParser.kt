package com.example.app

fun parseScenario(text: String): Scenario {
    val ops = mutableListOf<Op>()
    for (rawLine in text.lineSequence()) {
        val line = rawLine.trim()
        if (line.isEmpty()) continue
        val parts = line.split(Regex("\\s+"), limit = 5)
        when (parts[0]) {
            "BIND" -> {
                require(parts.size >= 5) { "BIND needs cell_id item_id title fetch_at_tick" }
                ops.add(Op.Bind(parts[1], parts[2], parts[3], parts[4].toLong()))
            }
            "RECYCLE" -> {
                require(parts.size >= 2) { "RECYCLE needs cell_id" }
                ops.add(Op.Recycle(parts[1]))
            }
            "RESOLVE" -> {
                require(parts.size >= 3) { "RESOLVE needs item_id image_url" }
                ops.add(Op.Resolve(parts[1], parts[2]))
            }
            "TICK" -> {
                require(parts.size >= 2) { "TICK needs new_now" }
                ops.add(Op.Tick(parts[1].toLong()))
            }
            "REFETCH" -> {
                require(parts.size >= 3) { "REFETCH needs cell_id fetch_at_tick" }
                ops.add(Op.Refetch(parts[1], parts[2].toLong()))
            }
            "QUERY" -> {
                require(parts.size >= 2) { "QUERY needs cell_id" }
                ops.add(Op.Query(parts[1]))
            }
        }
    }
    return Scenario(ops)
}
