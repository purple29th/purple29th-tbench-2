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
            fragment=Home parent=NONE hidden=false lifecycle=RESUMED viewModel={} savedState={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("add child requires parent") {
        val m = FragmentManager()
        m.begin("t1"); m.addChild("t1", "Ghost", "tab", "Child"); m.commit("t1")
        val snap = m.snapshot()
        // Child should NOT be added if parent missing
        assert(!snap.contains("Child")) { "Child added without parent" }
        results.add("add child requires parent" to "PASS")
    }

    run("child added with parent") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "homeTabs", "Tab1"); m.addToBackStack("t2", null); m.commit("t2")
        val snap = m.snapshot()
        expect("child added with parent",
            """
            container=homeTabs fragments=[Tab1]
            container=main fragments=[Home]
            fragment=Home parent=NONE hidden=false lifecycle=RESUMED viewModel={} savedState={} children=[Tab1]
            fragment=Tab1 parent=Home hidden=false lifecycle=RESUMED viewModel={} savedState={} children=[]
            backstack=[anon]
            """.trimIndent(),
            snap)
    }

    run("remove parent cascades to children") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "homeTabs", "Tab1"); m.commit("t2")
        m.begin("t3"); m.addChild("t3", "Tab1", "tabContainer", "Inner"); m.commit("t3")
        m.begin("t4"); m.remove("t4", "Home"); m.commit("t4")
        val snap = m.snapshot()
        // All should be gone
        val hasFragments = snap.contains("fragment=")
        if (hasFragments) {
            expect("remove parent cascades to children", "no fragments expected", snap)
        } else {
            results.add("remove parent cascades to children" to "PASS")
        }
    }

    run("hide downgrades lifecycle to STARTED") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.hide("t2", "Home"); m.commit("t2")
        val snap = m.snapshot()
        expect("hide downgrades lifecycle",
            """
            container=main fragments=[Home]
            fragment=Home parent=NONE hidden=true lifecycle=STARTED viewModel={} savedState={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("show upgrades lifecycle to RESUMED") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.hide("t2", "Home"); m.commit("t2")
        m.begin("t3"); m.show("t3", "Home"); m.commit("t3")
        val snap = m.snapshot()
        expect("show upgrades lifecycle",
            """
            container=main fragments=[Home]
            fragment=Home parent=NONE hidden=false lifecycle=RESUMED viewModel={} savedState={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("replace captures child tree for restore") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "homeTabs", "Tab1"); m.commit("t2")
        m.begin("t3"); m.replace("t3", "main", "Profile"); m.addToBackStack("t3", "profile"); m.commit("t3")
        // Now pop, Home should be restored with Tab1 child
        m.pop(null)
        val snap = m.snapshot()
        val hasHome = snap.contains("fragment=Home")
        val hasTab = snap.contains("fragment=Tab1") && snap.contains("parent=Home")
        if (hasHome && hasTab) results.add("replace captures child tree for restore" to "PASS")
        else expect("replace captures child tree for restore", "Home with Tab1 child expected", snap)
    }

    run("pop named uses indexOfLast") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "A"); m.addToBackStack("t2", "dup"); m.commit("t2")
        m.begin("t3"); m.replace("t3", "main", "B"); m.addToBackStack("t3", "other"); m.commit("t3")
        m.begin("t4"); m.replace("t4", "main", "C"); m.addToBackStack("t4", "dup"); m.commit("t4")
        // backstack = [dup, other, dup]  (first dup at bottom)
        // POP dup should pop only top-most dup, leaving [dup, other]
        m.pop("dup")
        val snap = m.snapshot()
        // should have B fragment and backstack [dup, other]
        val hasB = snap.contains("fragments=[B]")
        val hasBackstack = snap.contains("backstack=[dup, other]")
        if (hasB && hasBackstack) results.add("pop named uses indexOfLast" to "PASS")
        else expect("pop named uses indexOfLast", "fragments=[B] and backstack=[dup, other] expected", snap)
    }

    run("pop missing name is no-op") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.replace("t2", "main", "Profile"); m.addToBackStack("t2", "profile"); m.commit("t2")
        m.pop("ghost")
        val snap = m.snapshot()
        expect("pop missing name is no-op",
            """
            container=main fragments=[Profile]
            fragment=Profile parent=NONE hidden=false lifecycle=RESUMED viewModel={} savedState={} children=[]
            backstack=[profile]
            """.trimIndent(),
            snap)
    }

    run("rotate retains viewModel and child hierarchy") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.addToBackStack("t1", "home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "tabs", "Tab1"); m.addToBackStack("t2", null); m.commit("t2")
        m.putViewModel("Home", "vmKey", "vmVal")
        m.save("Home", "savedKey", "savedVal")
        m.rotate()
        val snap = m.snapshot()
        val hasVm = snap.contains("vmKey=vmVal")
        val hasSaved = snap.contains("savedKey=savedVal")
        val hasChild = snap.contains("fragment=Tab1") && snap.contains("parent=Home")
        val hasContainer = snap.contains("container=main") && snap.contains("Home")
        if (hasVm && hasSaved && hasChild && hasContainer) results.add("rotate retains viewModel and child hierarchy" to "PASS")
        else expect("rotate retains viewModel and child hierarchy", "vm, savedState and child expected", snap)
    }

    run("rotate drops non-backstacked") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1") // not backstacked
        m.begin("t2"); m.add("t2", "main", "Profile"); m.addToBackStack("t2", null); m.commit("t2")
        m.rotate()
        val snap = m.snapshot()
        // Home should be gone, only Profile
        val noHomeFrag = !snap.contains("fragment=Home")
        val hasProfile = snap.contains("Profile")
        if (noHomeFrag && hasProfile) results.add("rotate drops non-backstacked" to "PASS")
        else expect("rotate drops non-backstacked", "Home should be gone after rotate", snap)
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
