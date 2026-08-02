package com.example.fragment.test

import com.example.fragment.FragmentManager

private val results = mutableListOf<Pair<String, String>>()

private fun expect(name: String, expected: String, actual: String) {
    if (expected.trim() == actual.trim()) results.add(name to "PASS")
    else results.add(name to "FAIL\n  expected:\n${indent(expected)}\n  actual:\n${indent(actual)}")
}

private fun indent(s: String): String = s.lines().joinToString("\n") { "    $it" }

fun main() {
    run("smoke add empty") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        val snap = m.snapshot()
        val ok = snap.contains("container=main fragments=[Home]") && snap.contains("binding={}")
        if (ok) results.add("smoke add empty" to "PASS")
        else results.add("smoke add empty" to "FAIL\n $snap")
    }

    run("smoke binding put and clear on hide") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putBinding("Home", "bK", "bV")
        var snap = m.snapshot()
        val hasBinding = snap.contains("bK=bV")
        m.begin("t2"); m.hide("t2", "Home"); m.commit("t2")
        snap = m.snapshot()
        val cleared = !snap.contains("bK=bV") && snap.contains("binding={}") && snap.contains("hidden=true")
        if (hasBinding && cleared) results.add("smoke binding put and clear on hide" to "PASS")
        else results.add("smoke binding put and clear on hide" to "FAIL\n $snap")
    }

    run("smoke vm retained across hide") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putViewModel("Home", "vmK", "vmV")
        m.putBinding("Home", "bK", "bV")
        m.begin("t2"); m.hide("t2", "Home"); m.commit("t2")
        m.begin("t3"); m.show("t3", "Home"); m.commit("t3")
        val snap = m.snapshot()
        val hasVm = snap.contains("vmK=vmV")
        val noBinding = !snap.contains("bK=bV")
        if (hasVm && noBinding) results.add("smoke vm retained across hide" to "PASS")
        else results.add("smoke vm retained across hide" to "FAIL\n $snap")
    }

    run("smoke detach retains vm clears binding") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putViewModel("Home", "k", "v")
        m.putBinding("Home", "bk", "bv")
        m.begin("t2"); m.detach("t2", "Home"); m.commit("t2")
        val snap = m.snapshot()
        val hasVm = snap.contains("k=v")
        val noBk = !snap.contains("bk=bv") && snap.contains("binding={}")
        val detached = snap.contains("detached=true")
        if (hasVm && noBk && detached) results.add("smoke detach retains vm clears binding" to "PASS")
        else results.add("smoke detach retains vm clears binding" to "FAIL\n $snap")
    }

    run("smoke pop missing noop") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "Profile"); m.addToBackStack("t2", "profile"); m.commit("t2")
        m.pop("ghost")
        val snap = m.snapshot()
        val hasProfile = snap.contains("fragments=[Profile]")
        val hasStack = snap.contains("backstack=[profile]")
        if (hasProfile && hasStack) results.add("smoke pop missing noop" to "PASS")
        else results.add("smoke pop missing noop" to "FAIL\n $snap")
    }

    run("smoke rotate clears binding retains vm") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.addToBackStack("t1", "home"); m.commit("t1")
        m.putViewModel("Home", "vmK", "vmV")
        m.putBinding("Home", "bK", "bV")
        m.rotate()
        val snap = m.snapshot()
        val hasVm = snap.contains("vmK=vmV")
        val bindingEmpty = snap.contains("binding={}") && !snap.contains("bK=bV")
        val hasHome = snap.contains("fragment=Home")
        if (hasVm && bindingEmpty && hasHome) results.add("smoke rotate clears binding retains vm" to "PASS")
        else results.add("smoke rotate clears binding retains vm" to "FAIL\n $snap")
    }

    var allPass = true
    for ((name, status) in results) {
        if (status.startsWith("PASS")) println("PASS  $name")
        else { allPass = false; println("FAIL  $name"); println(status.lineSequence().drop(1).joinToString("\n")) }
    }
    if (allPass) println("\nAll contract tests pass.") else println("\nContract failures above.")
}

private fun run(name: String, block: () -> Unit) {
    try { block() } catch (e: Throwable) { results.add(name to "FAIL\n  exception: ${e.message}\n${e.stackTraceToString()}") }
}
