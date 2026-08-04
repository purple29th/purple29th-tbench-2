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
            "MOUNT" -> {
                if (parts.size >= 4) manager.mount(parts[1], parts[2], parts[3])
            }
            "UPDATE_KEY" -> {
                if (parts.size >= 3) manager.updateKey(parts[1], parts[2])
            }
            "VM_PUT" -> {
                if (parts.size >= 4) manager.vmPut(parts[1], parts[2], parts[3])
            }
            "REMEMBER_PUT" -> {
                if (parts.size >= 4) manager.rememberPut(parts[1], parts[2], parts[3])
            }
            "UNMOUNT" -> {
                if (parts.size >= 2) manager.unmount(parts[1])
            }
            "QUERY" -> {
                snapshots.add(manager.snapshot())
            }
        }
    }
    val out = snapshots.joinToString("\n\n")
    File("/app/output.txt").writeText(out)
}
