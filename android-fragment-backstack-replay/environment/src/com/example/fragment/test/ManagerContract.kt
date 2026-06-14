package com.example.fragment.test

import com.example.fragment.FragmentManager

private val results = mutableListOf<Pair<String, String>>()

private fun expect(name: String, expected: String, actual: String) {
    if (expected.trim() == actual.trim()) results.add(name to "PASS")
    else results.add(name to "FAIL\n  expected:\n${indent(expected)}\n  actual:\n${indent(actual)}")
}

private fun indent(s: String): String = s.lines().joinToString("\n") { "    $it" }

fun main() {
    run("scenario A") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        expect("scenario A",
            "container=main fragments=[Home]\nbackstack=[]\n",
            m.snapshot())
    }

    run("scenario B") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "Profile")
        m.addToBackStack("t2", "profile"); m.commit("t2")
        m.pop(null)
        expect("scenario B",
            "container=main fragments=[Home]\nbackstack=[]\n",
            m.snapshot())
    }

    run("scenario C") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "Settings")
        m.addToBackStack("t2", "settings"); m.commit("t2")
        m.begin("t3"); m.replace("t3", "main", "Profile")
        m.addToBackStack("t3", "profile"); m.commit("t3")
        m.pop("settings")
        expect("scenario C",
            "container=main fragments=[Home]\nbackstack=[]\n",
            m.snapshot())
    }

    run("scenario D") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "Profile")
        m.addToBackStack("t2", "profile"); m.commit("t2")
        m.pop("ghost")
        expect("scenario D",
            "container=main fragments=[Profile]\nbackstack=[profile]\n",
            m.snapshot())
    }

    run("scenario E") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "Profile")
        m.addToBackStack("t2", "profile"); m.commit("t2")
        m.rotate()
        expect("scenario E",
            "container=main fragments=[Profile]\nbackstack=[profile]\n",
            m.snapshot())
    }

    run("scenario F") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "Profile")
        m.addToBackStack("t2", null); m.commit("t2")
        expect("scenario F",
            "container=main fragments=[Profile]\nbackstack=[anon]\n",
            m.snapshot())
    }

    var allPass = true
    for ((name, status) in results) {
        if (status.startsWith("PASS")) println("PASS  $name")
        else { allPass = false; println("FAIL  $name"); println(status.lineSequence().drop(1).joinToString("\n")) }
    }
    if (allPass) println("\nAll contract tests pass.") else println("\nContract failures above.")
}

private fun run(name: String, block: () -> Unit) {
    try { block() } catch (e: Throwable) { results.add(name to "FAIL\n  exception: ${e.message}") }
}
