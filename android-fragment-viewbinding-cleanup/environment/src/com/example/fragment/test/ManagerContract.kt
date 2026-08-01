package com.example.fragment.test

import com.example.fragment.FragmentManager

private val results = mutableListOf<Pair<String, String>>()

private fun expect(name: String, expected: String, actual: String) {
    if (expected.trim() == actual.trim()) results.add(name to "PASS")
    else results.add(name to "FAIL\n  expected:\n${indent(expected)}\n  actual:\n${indent(actual)}")
}

private fun indent(s: String): String = s.lines().joinToString("\n") { "    $it" }

fun main() {
    run("simple add binding empty") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        val snap = m.snapshot()
        expect("simple add binding empty",
            """
            container=main fragments=[Home]
            fragment=Home parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} binding={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("bind put") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putBinding("Home", "bKey", "bVal")
        val snap = m.snapshot()
        expect("bind put",
            """
            container=main fragments=[Home]
            fragment=Home parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} binding={bKey=bVal} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("hide clears binding") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putBinding("Home", "bKey", "bVal")
        m.begin("t2"); m.hide("t2", "Home"); m.commit("t2")
        val snap = m.snapshot()
        expect("hide clears binding",
            """
            container=main fragments=[Home]
            fragment=Home parent=NONE hidden=true detached=false lifecycle=STARTED maxLifecycle=RESUMED viewModel={} savedState={} binding={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("hide show binding recreated empty") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putBinding("Home", "bKey", "bVal")
        m.begin("t2"); m.hide("t2", "Home"); m.commit("t2")
        m.begin("t3"); m.show("t3", "Home"); m.commit("t3")
        val snap = m.snapshot()
        expect("hide show binding recreated empty",
            """
            container=main fragments=[Home]
            fragment=Home parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} binding={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("viewModel retained across hide, binding not") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putViewModel("Home", "vmK", "vmV")
        m.putBinding("Home", "bK", "bV")
        m.begin("t2"); m.hide("t2", "Home"); m.commit("t2")
        m.begin("t3"); m.show("t3", "Home"); m.commit("t3")
        val snap = m.snapshot()
        val hasVm = snap.contains("vmK=vmV")
        val noBinding = !snap.contains("bK=bV") && snap.contains("binding={}")
        if (hasVm && noBinding) results.add("viewModel retained across hide, binding not" to "PASS")
        else expect("viewModel retained across hide, binding not", "vm retained binding empty", snap)
    }

    run("detach clears binding retains vm") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putViewModel("Home", "k", "v")
        m.putBinding("Home", "bk", "bv")
        m.save("Home", "s", "sv")
        m.begin("t2"); m.detach("t2", "Home"); m.commit("t2")
        val snap = m.snapshot()
        expect("detach clears binding retains vm",
            """
            container=main fragments=[]
            fragment=Home parent=NONE hidden=false detached=true lifecycle=CREATED maxLifecycle=RESUMED viewModel={k=v} savedState={s=sv} binding={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("detach attach binding empty vm retained") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putViewModel("Home", "k", "v")
        m.putBinding("Home", "bk", "bv")
        m.begin("t2"); m.detach("t2", "Home"); m.commit("t2")
        m.begin("t3"); m.attach("t3", "Home"); m.commit("t3")
        val snap = m.snapshot()
        expect("detach attach binding empty vm retained",
            """
            container=main fragments=[Home]
            fragment=Home parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={k=v} savedState={} binding={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("hide propagates binding clear to children") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "tabs", "Tab1"); m.commit("t2")
        m.putBinding("Tab1", "bk", "bv")
        m.begin("t3"); m.hide("t3", "Home"); m.commit("t3")
        val snap = m.snapshot()
        val tabBindingEmpty = snap.contains("fragment=Tab1") && snap.contains("binding={}")
        val childHasNoBinding = !snap.contains("bk=bv")
        if (tabBindingEmpty && childHasNoBinding) results.add("hide propagates binding clear to children" to "PASS")
        else expect("hide propagates binding clear to children", "child binding should be cleared on parent hide", snap)
    }

    run("show propagates binding empty to children") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "tabs", "Tab1"); m.commit("t2")
        m.begin("t3"); m.hide("t3", "Home"); m.commit("t3")
        m.begin("t4"); m.show("t4", "Home"); m.commit("t4")
        val snap = m.snapshot()
        // after show, both Home and Tab1 binding should be empty
        val hasBindingsEmpty = snap.contains("fragment=Home") && snap.contains("fragment=Tab1") && snap.split("binding=").size >= 3
        // check both fragments have empty binding
        val lines = snap.lines().filter { it.startsWith("fragment=") }
        val allEmpty = lines.all { it.contains("binding={}") }
        if (allEmpty) results.add("show propagates binding empty to children" to "PASS")
        else expect("show propagates binding empty to children", "all bindings should be empty after show", snap)
    }

    run("rotate clears binding retains vm savedState") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.addToBackStack("t1", "home"); m.commit("t1")
        m.putViewModel("Home", "vmK", "vmV")
        m.save("Home", "sK", "sV")
        m.putBinding("Home", "bK", "bV")
        m.rotate()
        val snap = m.snapshot()
        val hasVm = snap.contains("vmK=vmV")
        val hasSaved = snap.contains("sK=sV")
        val bindingEmpty = snap.contains("binding={}") && !snap.contains("bK=bV")
        val hasHome = snap.contains("fragment=Home")
        if (hasVm && hasSaved && bindingEmpty && hasHome) results.add("rotate clears binding retains vm savedState" to "PASS")
        else expect("rotate clears binding retains vm savedState", "vm and savedState retained, binding empty after rotate", snap)
    }

    run("rotate drops non backstacked binding") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putBinding("Home", "bK", "bV")
        m.begin("t2"); m.add("t2", "main", "Other"); m.addToBackStack("t2", "bs"); m.commit("t2")
        m.rotate()
        val snap = m.snapshot()
        val noHome = !snap.contains("fragment=Home")
        val hasOther = snap.contains("fragment=Other")
        val otherBindingEmpty = snap.contains("fragment=Other") && snap.contains("binding={}")
        if (noHome && hasOther && otherBindingEmpty) results.add("rotate drops non backstacked binding" to "PASS")
        else expect("rotate drops non backstacked binding", "Home should be dropped, Other binding empty", snap)
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
            fragment=Profile parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} binding={} children=[]
            backstack=[profile]
            """.trimIndent(),
            snap)
    }

    run("replace clears binding of old") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putBinding("Home", "bk", "bv")
        m.begin("t2"); m.replace("t2", "main", "Profile"); m.commit("t2")
        val snap = m.snapshot()
        val hasProfile = snap.contains("fragment=Profile")
        val noHome = !snap.contains("fragment=Home")
        if (hasProfile && noHome) results.add("replace clears binding of old" to "PASS")
        else expect("replace clears binding of old", "Profile only, Home gone", snap)
    }

    run("replace child binding cleared on parent replace") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "tabs", "Tab1"); m.commit("t2")
        m.putBinding("Tab1", "bk", "bv")
        m.begin("t3"); m.replace("t3", "main", "Other"); m.commit("t3")
        val snap = m.snapshot()
        val noTab = !snap.contains("fragment=Tab1")
        if (noTab) results.add("replace child binding cleared on parent replace" to "PASS")
        else expect("replace child binding cleared on parent replace", "Tab1 should be removed with parent", snap)
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
