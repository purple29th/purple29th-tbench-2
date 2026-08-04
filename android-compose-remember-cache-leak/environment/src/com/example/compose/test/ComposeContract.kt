package com.example.compose.test

import com.example.compose.ComposeManager

fun main() {
    val m = ComposeManager()
    m.mount("root","NONE","k1")
    m.rememberPut("root","r1","c1")
    var snap = m.snapshot()
    check(snap.contains("node=root")) { "root missing" }
    check(snap.contains("remember={r1=c1}")) { "remember not set" }
    m.vmPut("root","vm1","v1")
    m.updateKey("root","k2")
    snap = m.snapshot()
    check(snap.contains("remember={}")) { "remember not cleared on update" }
    check(snap.contains("viewModel={vm1=v1}")) { "vm should survive update" }
    m.mount("child","root","k1")
    m.rememberPut("child","rc","cc")
    m.updateKey("root","k3")
    snap = m.snapshot()
    check(snap.contains("node=child") && snap.contains("remember={}")) { "child remember not cleared on parent update" }
    m.unmount("root")
    snap = m.snapshot()
    check(snap.isEmpty()) { "unmount should clear all" }
    m.mount("child2","missingParent","k1")
    snap = m.snapshot()
    check(!snap.contains("child2")) { "should ignore mount with missing parent" }
    m.mount("root","NONE","k1")
    m.rememberPut("root","r1","c1")
    m.updateKey("root","k1")
    snap = m.snapshot()
    check(snap.contains("remember={r1=c1}")) { "same key should not clear" }
    println("All contract tests pass")
}
