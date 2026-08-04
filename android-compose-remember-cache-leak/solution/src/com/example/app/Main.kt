package com.example.app

import com.example.compose.ComposeManager
import java.io.File

fun main() {
    val scenarioText = File("/app/scenario.txt").readText()
    val manager = ComposeManager()
    val snapshots = mutableListOf<String>()
    for (rawLine in scenarioText.lines()) {
        val line = rawLine.trim()
        if (line.isEmpty() || line.startsWith("#")) continue
        val parts = line.split(" ")
        when (parts[0]) {
            "BEGIN" -> if (parts.size >= 2) manager.begin(parts[1])
            "ADD_TO_BACKSTACK" -> if (parts.size >= 3) manager.addToBackstack(parts[1], parts[2])
            "COMMIT" -> if (parts.size >= 2) manager.commit(parts[1])
            "POP" -> manager.pop(if (parts.size >= 2) parts[1] else "NONE")
            "MOUNT" -> if (parts.size >= 5) manager.mount(parts[1], parts[2], parts[3], parts[4])
            "UPDATE_KEY" -> if (parts.size >= 4) manager.updateKey(parts[1], parts[2], parts[3])
            "HIDE" -> if (parts.size >= 3) manager.hide(parts[1], parts[2])
            "SHOW" -> if (parts.size >= 3) manager.show(parts[1], parts[2])
            "UNMOUNT" -> if (parts.size >= 3) manager.unmount(parts[1], parts[2])
            "VM_PUT" -> if (parts.size >= 4) manager.vmPut(parts[1], parts[2], parts[3])
            "REMEMBER_PUT" -> if (parts.size >= 4) manager.rememberPut(parts[1], parts[2], parts[3])
            "SAVE" -> if (parts.size >= 4) manager.savePut(parts[1], parts[2], parts[3])
            "ROTATE" -> manager.rotate()
            "QUERY" -> snapshots.add(manager.snapshot())
        }
    }
    val out = snapshots.joinToString("\n\n")
    File("/app/output.txt").writeText(out)
}
