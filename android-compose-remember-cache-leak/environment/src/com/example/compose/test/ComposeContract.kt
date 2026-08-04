package com.example.compose.test

import com.example.compose.ComposeManager

fun main() {
    val m = ComposeManager()
    // use transactions
    m.begin("t1")
    m.mount("t1","root","NONE","k1")
    m.commit("t1")
    m.rememberPut("root","r1","c1")
    var snap = m.snapshot()
    check(snap.contains("node=root")) { "root missing $snap" }
    check(snap.contains("remember={r1=c1}")) { "remember not set $snap" }
    m.vmPut("root","vm1","v1")
    m.begin("t2")
    m.updateKey("t2","root","k2")
    m.commit("t2")
    snap = m.snapshot()
    check(snap.contains("remember={}")) { "remember not cleared on update $snap" }
    check(snap.contains("viewModel={vm1=v1}")) { "vm should survive update $snap" }
    m.begin("t3")
    m.mount("t3","child","root","k1")
    m.commit("t3")
    m.rememberPut("child","rc","cc")
    m.begin("t4")
    m.updateKey("t4","root","k3")
    m.commit("t4")
    snap = m.snapshot()
    check(snap.contains("node=child") && snap.contains("remember={}")) { "child remember not cleared on parent update $snap" }
    m.begin("t5")
    m.unmount("t5","root")
    m.commit("t5")
    snap = m.snapshot()
    check(snap.isEmpty()) { "unmount should clear all $snap" }
    m.begin("t6")
    m.mount("t6","child2","missingParent","k1")
    m.commit("t6")
    snap = m.snapshot()
    check(!snap.contains("child2")) { "should ignore mount with missing parent $snap" }
    m.begin("t7")
    m.mount("t7","root","NONE","k1")
    m.commit("t7")
    m.rememberPut("root","r1","c1")
    m.begin("t8")
    m.updateKey("t8","root","k1")
    m.commit("t8")
    snap = m.snapshot()
    check(snap.contains("remember={r1=c1}")) { "same key should not clear $snap" }
    // test hide/show cascade
    m.begin("t9")
    m.mount("t9","child","root","k1")
    m.commit("t9")
    m.rememberPut("child","rChild","cChild")
    m.begin("t10")
    m.hide("t10","root")
    m.commit("t10")
    snap = m.snapshot()
    check(snap.contains("hidden") && snap.contains("remember={}")) { "hide should clear remember and mark hidden $snap" }
    m.begin("t11")
    m.show("t11","root")
    m.commit("t11")
    snap = m.snapshot()
    check(!snap.contains("hidden")) { "show should unhide $snap" }
    // test rotate
    m.rememberPut("root","r1","c1")
    m.rotate()
    snap = m.snapshot()
    check(snap.contains("remember={}")) { "rotate should clear remember $snap" }
    check(snap.contains("viewModel={vm1=v1}")) { "rotate should keep vm $snap" }
    // test parent in same txn
    m.begin("t12")
    m.mount("t12","parent2","NONE","kp")
    m.mount("t12","childSameTxn","parent2","kc")
    m.commit("t12")
    snap = m.snapshot()
    check(snap.contains("node=childSameTxn") && snap.contains("node=parent2")) { "mount child where parent mounted earlier in same txn should succeed $snap" }
    println("All contract tests pass")
}
