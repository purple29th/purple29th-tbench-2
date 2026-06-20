package com.example.app

import com.example.recycler.FetchScheduler
import com.example.recycler.RecyclerPool
import java.io.File

fun main() {
    val scenarioText = File("/app/scenario.json").readText()
    val scenario = parseScenario(scenarioText)
    val output = runScenario(scenario)
    File("/app/output.txt").writeText(output)
}

fun runScenario(scenario: Scenario): String {
    val pool = RecyclerPool()
    val scheduler = FetchScheduler(pool)
    val querySnapshots = mutableListOf<String>()

    for (op in scenario.ops) {
        when (op) {
            is Op.Bind -> {
                val token = pool.bind(op.cellId, op.itemId, op.title)
                scheduler.schedule(op.cellId, op.itemId, token, op.fetchAt)
            }
            is Op.Recycle -> pool.recycle(op.cellId)
            is Op.Resolve -> scheduler.queueResolution(op.itemId, op.imageUrl)
            is Op.Tick -> scheduler.advance(op.now)
            is Op.Query -> querySnapshots.add(pool.snapshot(op.cellId))
            is Op.Refetch -> {
                val cell = pool.cell(op.cellId)
                val itemId = cell.itemId
                if (itemId != null) scheduler.schedule(op.cellId, itemId, cell.bindingToken, op.fetchAt)
            }
        }
    }

    return querySnapshots.joinToString(separator = "\n", postfix = "\n")
}
