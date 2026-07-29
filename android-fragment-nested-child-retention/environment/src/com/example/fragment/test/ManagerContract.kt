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
            fragment=Home parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("add child requires parent") {
        val m = FragmentManager()
        m.begin("t1"); m.addChild("t1", "Ghost", "tab", "Child"); m.commit("t1")
        val snap = m.snapshot()
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
            fragment=Home parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} children=[Tab1]
            fragment=Tab1 parent=Home hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} children=[]
            backstack=[anon]
            """.trimIndent(),
            snap)
    }

    run("remove parent cascades") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "homeTabs", "Tab1"); m.commit("t2")
        m.begin("t3"); m.addChild("t3", "Tab1", "tabContainer", "Inner"); m.commit("t3")
        m.begin("t4"); m.remove("t4", "Home"); m.commit("t4")
        val snap = m.snapshot()
        val hasFragments = snap.contains("fragment=")
        if (hasFragments) {
            expect("remove parent cascades", "no fragments expected", snap)
        } else {
            results.add("remove parent cascades" to "PASS")
        }
    }

    run("hide downgrades") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.hide("t2", "Home"); m.commit("t2")
        val snap = m.snapshot()
        expect("hide downgrades",
            """
            container=main fragments=[Home]
            fragment=Home parent=NONE hidden=true detached=false lifecycle=STARTED maxLifecycle=RESUMED viewModel={} savedState={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("show upgrades") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.hide("t2", "Home"); m.commit("t2")
        m.begin("t3"); m.show("t3", "Home"); m.commit("t3")
        val snap = m.snapshot()
        expect("show upgrades",
            """
            container=main fragments=[Home]
            fragment=Home parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} children=[]
            backstack=[]
            """.trimIndent(),
            snap)
    }

    run("replace captures child tree") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "homeTabs", "Tab1"); m.commit("t2")
        m.begin("t3"); m.replace("t3", "main", "Profile"); m.addToBackStack("t3", "profile"); m.commit("t3")
        m.pop(null)
        val snap = m.snapshot()
        val hasHome = snap.contains("fragment=Home")
        val hasTab = snap.contains("fragment=Tab1") && snap.contains("parent=Home")
        if (hasHome && hasTab) results.add("replace captures child tree" to "PASS")
        else expect("replace captures child tree", "Home with Tab1 child expected", snap)
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
            fragment=Profile parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} children=[]
            backstack=[profile]
            """.trimIndent(),
            snap)
    }

    run("rotate retains vm child") {
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
        if (hasVm && hasSaved && hasChild) results.add("rotate retains vm child" to "PASS")
        else expect("rotate retains vm child", "vm savedState child expected", snap)
    }

    run("rotate drops non bs") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.add("t2", "main", "Profile"); m.addToBackStack("t2", null); m.commit("t2")
        m.rotate()
        val snap = m.snapshot()
        val noHomeFrag = !snap.contains("fragment=Home")
        val hasProfile = snap.contains("Profile")
        if (noHomeFrag && hasProfile) results.add("rotate drops non bs" to "PASS")
        else expect("rotate drops non bs", "Home should be gone", snap)
    }

    run("viewModel cleared on remove") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putViewModel("Home", "vmKey", "vmVal")
        m.begin("t2"); m.remove("t2", "Home"); m.commit("t2")
        m.begin("t3"); m.add("t3", "main", "Home"); m.commit("t3")
        val snap = m.snapshot()
        val hasEmptyVm = snap.contains("fragment=Home") && !snap.contains("vmKey=vmVal")
        if (hasEmptyVm) results.add("viewModel cleared on remove" to "PASS")
        else expect("viewModel cleared on remove", "empty vm expected", snap)
    }

    run("viewModel cleared on parent remove") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "tabs", "Tab1"); m.commit("t2")
        m.putViewModel("Tab1", "vmKey", "vmVal")
        m.begin("t3"); m.remove("t3", "Home"); m.commit("t3")
        m.begin("t4"); m.add("t4", "main", "Home"); m.commit("t4")
        m.begin("t5"); m.addChild("t5", "Home", "tabs", "Tab1"); m.commit("t5")
        val snap = m.snapshot()
        val hasEmptyVm = snap.contains("fragment=Tab1") && !snap.contains("vmKey=vmVal")
        if (hasEmptyVm) results.add("viewModel cleared on parent remove" to "PASS")
        else expect("viewModel cleared on parent remove", "empty vm expected", snap)
    }

    run("set max cascades") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "tabs", "Tab1"); m.commit("t2")
        m.begin("t3"); m.addChild("t3", "Tab1", "inner", "Inner"); m.commit("t3")
        m.begin("t4"); m.setMax("t4", "Home", "STARTED"); m.commit("t4")
        val snap = m.snapshot()
        val homeStarted = snap.contains("fragment=Home") && snap.contains("lifecycle=STARTED") && snap.contains("maxLifecycle=STARTED")
        val tabCap = snap.contains("fragment=Tab1") && snap.contains("maxLifecycle=STARTED")
        if (homeStarted && tabCap) results.add("set max cascades" to "PASS")
        else expect("set max cascades", "max should cascade to children", snap)
    }

    run("set max blocks resumed") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setMax("t2", "Home", "STARTED"); m.commit("t2")
        m.begin("t3"); m.addChild("t3", "Home", "tabs", "Tab1"); m.commit("t3")
        val snap = m.snapshot()
        val tabNotResumed = snap.contains("fragment=Tab1") && snap.contains("lifecycle=STARTED")
        if (tabNotResumed) results.add("set max blocks resumed" to "PASS")
        else expect("set max blocks resumed", "child should be STARTED when parent max STARTED", snap)
    }

    run("detach retains vm") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.putViewModel("Home", "k", "v")
        m.save("Home", "s", "sv")
        m.begin("t2"); m.detach("t2", "Home"); m.commit("t2")
        val snap = m.snapshot()
        val detached = snap.contains("detached=true") && snap.contains("lifecycle=CREATED") && snap.contains("k=v")
        val noContainer = snap.contains("container=main fragments=[]")
        if (detached && noContainer) results.add("detach retains vm" to "PASS")
        else expect("detach retains vm", "detached CREATED with vm retained and empty container", snap)
    }

    run("detach attach restores") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.addChild("t2", "Home", "tabs", "Tab1"); m.commit("t2")
        m.putViewModel("Home", "k", "v")
        m.begin("t3"); m.detach("t3", "Home"); m.commit("t3")
        m.begin("t4"); m.attach("t4", "Home"); m.commit("t4")
        val snap = m.snapshot()
        val hasHome = snap.contains("fragment=Home") && snap.contains("detached=false") && snap.contains("k=v")
        val hasTab = snap.contains("fragment=Tab1")
        val hasContainer = snap.contains("container=main fragments=[Home]")
        if (hasHome && hasTab && hasContainer) results.add("detach attach restores" to "PASS")
        else expect("detach attach restores", "home restored with child and vm", snap)
    }

    run("hide with max") {
        val m = FragmentManager()
        m.begin("t1"); m.add("t1", "main", "Home"); m.commit("t1")
        m.begin("t2"); m.setMax("t2", "Home", "STARTED"); m.commit("t2")
        m.begin("t3"); m.hide("t3", "Home"); m.commit("t3")
        m.begin("t4"); m.show("t4", "Home"); m.commit("t4")
        val snap = m.snapshot()
        val ok = snap.contains("fragment=Home") && snap.contains("lifecycle=STARTED") && snap.contains("maxLifecycle=STARTED")
        if (ok) results.add("hide with max" to "PASS")
        else expect("hide with max", "should stay STARTED due to max", snap)
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
