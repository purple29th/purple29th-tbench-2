package com.example.app

import com.example.fragment.FragmentManager
import java.io.File

fun main() {
    val scenarioText = File("/app/scenario.txt").readText()
    val scenario = parseScenario(scenarioText)
    val output = runScenario(scenario)
    File("/app/output.txt").writeText(output)
}

fun runScenario(scenario: Scenario): String {
    val manager = FragmentManager()
    val snapshots = mutableListOf<String>()

    for (op in scenario.ops) {
        when (op) {
            is Op.Begin -> manager.begin(op.txnId)
            is Op.Add -> manager.add(op.txnId, op.container, op.fragment)
            is Op.AddChild -> manager.addChild(op.txnId, op.parent, op.childContainer, op.childFragment)
            is Op.Replace -> manager.replace(op.txnId, op.container, op.fragment)
            is Op.Remove -> manager.remove(op.txnId, op.fragment)
            is Op.Hide -> manager.hide(op.txnId, op.fragment)
            is Op.Show -> manager.show(op.txnId, op.fragment)
            is Op.Save -> manager.save(op.fragment, op.key, op.value)
            is Op.VmPut -> manager.putViewModel(op.fragment, op.key, op.value)
            is Op.AddToBackStack -> manager.addToBackStack(op.txnId, op.name)
            is Op.Commit -> manager.commit(op.txnId)
            is Op.Pop -> manager.pop(op.name)
            is Op.Rotate -> manager.rotate()
            is Op.Query -> snapshots.add(manager.snapshot())
        }
    }

    return snapshots.joinToString("\n\n")
}
