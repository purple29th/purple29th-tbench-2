package com.example.recycler.test

import com.example.recycler.FetchScheduler
import com.example.recycler.RecyclerPool

private val results = mutableListOf<Pair<String, String>>()

private fun expect(name: String, expected: String, actual: String) {
    if (expected == actual) results.add(name to "PASS")
    else results.add(name to "FAIL\n  expected: $expected\n  actual:   $actual")
}

private fun fixture(): Pair<RecyclerPool, FetchScheduler> {
    val pool = RecyclerPool()
    val scheduler = FetchScheduler(pool)
    return pool to scheduler
}

fun main() {
    run("simple bind then resolve") {
        val (pool, scheduler) = fixture()
        val token = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", token, 10)
        scheduler.queueResolution("itemA", "img://A")
        scheduler.advance(20)
        expect("simple bind then resolve",
            "c1 item=itemA title=Alice imageUrl=img://A",
            pool.snapshot("c1"))
    }

    run("recycle invalidates pending fetch") {
        val (pool, scheduler) = fixture()
        val token = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", token, 10)
        scheduler.queueResolution("itemA", "img://A")
        pool.recycle("c1")
        scheduler.advance(20)
        expect("recycle invalidates pending fetch",
            "c1 unbound",
            pool.snapshot("c1"))
    }

    run("rebind to different item invalidates previous fetch") {
        val (pool, scheduler) = fixture()
        val tokenA = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", tokenA, 10)
        scheduler.queueResolution("itemA", "img://A")
        pool.bind("c1", "itemB", "Bob")
        scheduler.advance(20)
        expect("rebind to different item invalidates previous fetch",
            "c1 item=itemB title=Bob imageUrl=NONE",
            pool.snapshot("c1"))
    }

    run("recycle then rebind to same item still invalidates older fetch") {
        val (pool, scheduler) = fixture()
        val tokenA = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", tokenA, 10)
        scheduler.queueResolution("itemA", "img://A_old")
        pool.recycle("c1")
        pool.bind("c1", "itemA", "Alice")
        scheduler.advance(20)
        expect("same-item rebind ignores stale fetch",
            "c1 item=itemA title=Alice imageUrl=NONE",
            pool.snapshot("c1"))
    }

    run("new fetch after rebind resolves correctly") {
        val (pool, scheduler) = fixture()
        val tokenA = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", tokenA, 10)
        scheduler.queueResolution("itemA", "img://A_old")
        val tokenB = pool.bind("c1", "itemB", "Bob")
        scheduler.schedule("c1", "itemB", tokenB, 15)
        scheduler.queueResolution("itemB", "img://B")
        scheduler.advance(20)
        expect("new fetch after rebind resolves correctly",
            "c1 item=itemB title=Bob imageUrl=img://B",
            pool.snapshot("c1"))
    }

    run("two cells resolve independently in scheduled order") {
        val (pool, scheduler) = fixture()
        val t1 = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", t1, 10)
        scheduler.queueResolution("itemA", "img://A")
        val t2 = pool.bind("c2", "itemB", "Bob")
        scheduler.schedule("c2", "itemB", t2, 10)
        scheduler.queueResolution("itemB", "img://B")
        scheduler.advance(20)
        expect("two cells: c1",
            "c1 item=itemA title=Alice imageUrl=img://A",
            pool.snapshot("c1"))
        expect("two cells: c2",
            "c2 item=itemB title=Bob imageUrl=img://B",
            pool.snapshot("c2"))
    }

    var allPass = true
    for ((name, status) in results) {
        if (status.startsWith("PASS")) {
            println("PASS  $name")
        } else {
            allPass = false
            println("FAIL  $name")
            println(status.lineSequence().drop(1).joinToString("\n"))
        }
    }
    if (allPass) println("\nAll contract tests pass.")
    else println("\nContract failures above.")
}

private fun run(name: String, block: () -> Unit) {
    try { block() } catch (e: Throwable) { results.add(name to "FAIL\n  exception: ${e.message}") }
}
