package com.example.fragment.test

import com.example.fragment.FragmentManager

private val results = mutableListOf<Pair<String, String>>()

private fun expect(name: String, expected: String, actual: String) {
    if (expected.trim() == actual.trim()) results.add(name to "PASS")
    else results.add(name to "FAIL\n  expected:\n${indent(expected)}\n  actual:\n${indent(actual)}")
}

private fun indent(s: String): String = s.lines().joinToString("\n") { "    $it" }

fun main() {
    run("simple add") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        val snap = m.snapshot()
        expect("simple add",
            """
            container=main fragments=[Home]
            fragment=Home listeners=[] pending={} delivered={}
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("listener registration") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResultListener("t2", "Home", "reqKey"); m.commit("t2")
        val snap = m.snapshot()
        expect("listener registration",
            """
            container=main fragments=[Home]
            fragment=Home listeners=[reqKey] pending={} delivered={}
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("result delivered when listener exists") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResultListener("t2", "Home", "k1"); m.commit("t2")
        m.begin("t3"); m.setResult("t3", "Home", "k1", "v1"); m.commit("t3")
        val snap = m.snapshot()
        expect("result delivered when listener exists",
            """
            container=main fragments=[Home]
            fragment=Home listeners=[] pending={} delivered={k1=v1}
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("result queued when no listener") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResult("t2", "Home", "k1", "v1"); m.commit("t2")
        val snap = m.snapshot()
        expect("result queued when no listener",
            """
            container=main fragments=[Home]
            fragment=Home listeners=[] pending={k1=v1} delivered={}
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("pending delivered when listener added later") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResult("t2", "Home", "k1", "v1"); m.commit("t2")
        m.begin("t3"); m.setResultListener("t3", "Home", "k1"); m.commit("t3")
        val snap = m.snapshot()
        expect("pending delivered when listener added later",
            """
            container=main fragments=[Home]
            fragment=Home listeners=[] pending={} delivered={k1=v1}
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("clear listener") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResultListener("t2", "Home", "k1"); m.commit("t2")
        m.begin("t3"); m.clearResultListener("t3", "Home", "k1"); m.commit("t3")
        val snap = m.snapshot()
        expect("clear listener",
            """
            container=main fragments=[Home]
            fragment=Home listeners=[] pending={} delivered={}
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("remove clears listeners and pending") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResultListener("t2", "Home", "k1"); m.commit("t2")
        m.begin("t3"); m.setResult("t3", "Home", "k1", "v1"); m.commit("t3")
        m.begin("t4"); m.remove("t4", "Home"); m.commit("t4")
        val snap = m.snapshot()
        // after remove, no fragment lines
        val noFrag = !snap.contains("fragment=")
        if (noFrag) results.add("remove clears listeners and pending" to "PASS")
        else expect("remove clears listeners and pending", "no fragment expected", snap)
    }

    run("replace captures result state") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResultListener("t2", "Home", "k1"); m.commit("t2")
        m.begin("t3"); m.setResult("t3", "Home", "k1", "v1"); m.commit("t3")
        m.begin("t4"); m.replace("t4", "main", "Profile"); m.addToBackStack("t4", "profile"); m.commit("t4")
        m.pop(null)
        val snap = m.snapshot()
        val hasHome = snap.contains("fragment=Home") && snap.contains("delivered={k1=v1}")
        if (hasHome) results.add("replace captures result state" to "PASS")
        else expect("replace captures result state", "Home with delivered result expected", snap)
    }

    run("pop named uses last") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "A"); m.addToBackStack("t2", "dup"); m.commit("t2")
        m.begin("t3"); m.replace("t3", "main", "B"); m.addToBackStack("t3", "other"); m.commit("t3")
        m.begin("t4"); m.replace("t4", "main", "C"); m.addToBackStack("t4", "dup"); m.commit("t4")
        m.pop("dup")
        val snap = m.snapshot()
        val hasB = snap.contains("fragments=[B]")
        val hasBackstack = snap.contains("backstack=[dup, other]")
        if (hasB && hasBackstack) results.add("pop named uses last" to "PASS")
        else expect("pop named uses last", "fragments=[B] and backstack=[dup, other] expected", snap)
    }

    run("pop missing is noop") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "Profile"); m.addToBackStack("t2", "profile"); m.commit("t2")
        m.pop("ghost")
        val snap = m.snapshot()
        expect("pop missing is noop",
            """
            container=main fragments=[Profile]
            fragment=Profile listeners=[] pending={} delivered={}
            backstack=[profile]
            """.trimIndent(),
            snap)
    }

    run("rotate retains listeners and pending for backstacked") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.addToBackStack("t1", "home"); m.commit("t1")
        m.begin("t2"); m.setResultListener("t2", "Home", "k1"); m.addToBackStack("t2", "listener"); m.commit("t2")
        m.begin("t3"); m.setResult("t3", "Home", "k1", "v1"); m.commit("t3")
        m.rotate()
        val snap = m.snapshot()
        val hasHome = snap.contains("fragment=Home")
        val hasListenerOrDelivered = snap.contains("listeners=[k1]") || snap.contains("delivered={k1=v1}")
        if (hasHome && hasListenerOrDelivered) results.add("rotate retains listeners and pending for backstacked" to "PASS")
        else expect("rotate retains listeners and pending for backstacked", "Home should survive rotate with listener or delivered", snap)
    }

    run("rotate drops non backstacked result") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setResultListener("t2", "Home", "k1"); m.commit("t2")
        m.rotate()
        val snap = m.snapshot()
        val noHome = !snap.contains("fragment=Home")
        if (noHome) results.add("rotate drops non backstacked result" to "PASS")
        else expect("rotate drops non backstacked result", "Home should be dropped after rotate because not backstacked", snap)
    }

    run("queued result survives rotate if backstacked") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.addToBackStack("t1", "home"); m.commit("t1")
        m.begin("t2"); m.setResult("t2", "Home", "k1", "v1"); m.addToBackStack("t2", "result"); m.commit("t2")
        m.rotate()
        val snap = m.snapshot()
        val hasPending = snap.contains("pending={k1=v1}") || snap.contains("delivered={k1=v1}")
        if (hasPending) results.add("queued result survives rotate if backstacked" to "PASS")
        else expect("queued result survives rotate if backstacked", "pending or delivered should survive rotate", snap)
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
