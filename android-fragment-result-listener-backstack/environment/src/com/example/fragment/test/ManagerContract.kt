package com.example.fragment.test

import com.example.fragment.FragmentManager

private val results = mutableListOf<Pair<String, String>>()

fun main() {
    run("smoke simple add") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        val snap = m.snapshot()
        val ok = snap.contains("container=main fragments=[Home]") && snap.contains("listeners=[]")
        if (ok) results.add("smoke simple add" to "PASS") else results.add("smoke simple add" to "FAIL\n$snap")
    }

    run("smoke result delivered") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResultListener("t2", "Home", "k1"); m.commit("t2")
        m.begin("t3"); m.setResult("t3", "Home", "k1", "v1"); m.commit("t3")
        val snap = m.snapshot()
        val ok = snap.contains("delivered={k1=v1}") && !snap.contains("pending={k1=")
        if (ok) results.add("smoke result delivered" to "PASS") else results.add("smoke result delivered" to "FAIL\n$snap")
    }

    run("smoke queued and later delivered") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResult("t2", "Home", "k1", "v1"); m.commit("t2")
        var snap = m.snapshot()
        val hasPending = snap.contains("pending={k1=v1}")
        m.begin("t3"); m.setResultListener("t3", "Home", "k1"); m.commit("t3")
        snap = m.snapshot()
        val delivered = snap.contains("delivered={k1=v1}") && !snap.contains("pending={k1=")
        if (hasPending && delivered) results.add("smoke queued and later delivered" to "PASS") else results.add("smoke queued and later delivered" to "FAIL\n$snap")
    }

    run("smoke pop missing noop") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "Profile"); m.addToBackStack("t2", "profile"); m.commit("t2")
        m.pop("ghost")
        val snap = m.snapshot()
        val ok = snap.contains("fragments=[Profile]") && snap.contains("backstack=[profile]")
        if (ok) results.add("smoke pop missing noop" to "PASS") else results.add("smoke pop missing noop" to "FAIL\n$snap")
    }

    run("smoke rotate drops non backstacked") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResultListener("t2", "Home", "k1"); m.commit("t2")
        m.rotate()
        val snap = m.snapshot()
        val noHome = !snap.contains("fragment=Home")
        if (noHome) results.add("smoke rotate drops non backstacked" to "PASS") else results.add("smoke rotate drops non backstacked" to "FAIL\n$snap")
    }

    var allPass = true
    for ((name, status) in results) {
        if (status.startsWith("PASS")) println("PASS  $name")
        else { allPass = false; println("FAIL  $name"); println(status.lineSequence().drop(1).joinToString("\n")) }
    }
    if (allPass) {
        println("\nAll contract tests pass.")
    } else {
        println("\nContract failures above.")
        kotlin.system.exitProcess(1)
    }
}

private fun run(name: String, block: () -> Unit) {
    try { block() } catch (e: Throwable) { results.add(name to "FAIL\n  exception: ${e.message}\n${e.stackTraceToString()}") }
}
