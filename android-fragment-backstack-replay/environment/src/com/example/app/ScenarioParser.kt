package com.example.app

fun parseScenario(text: String): Scenario {
    val ops = mutableListOf<Op>()
    for (rawLine in text.lineSequence()) {
        val line = rawLine.trim()
        if (line.isEmpty()) continue
        val parts = line.split(Regex("\\s+"))
        when (parts[0]) {
            "BEGIN" -> ops.add(Op.Begin(parts[1]))
            "ADD" -> ops.add(Op.Add(parts[1], parts[2], parts[3]))
            "REPLACE" -> ops.add(Op.Replace(parts[1], parts[2], parts[3]))
            "REMOVE" -> ops.add(Op.Remove(parts[1], parts[2]))
            "ADD_TO_BACK_STACK" -> {
                val name = if (parts[2] == "NONE") null else parts[2]
                ops.add(Op.AddToBackStack(parts[1], name))
            }
            "COMMIT" -> ops.add(Op.Commit(parts[1]))
            "POP" -> {
                val name = if (parts[1] == "NONE") null else parts[1]
                ops.add(Op.Pop(name))
            }
            "ROTATE" -> ops.add(Op.Rotate)
            "QUERY" -> ops.add(Op.Query)
        }
    }
    return Scenario(ops)
}
