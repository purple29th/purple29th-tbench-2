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
    run("scenario A") {
        val (pool, scheduler) = fixture()
        val token = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", token, 10)
        scheduler.queueResolution("itemA", "img://A")
        scheduler.advance(20)
        expect("scenario A",
            "c1 item=itemA title=Alice imageUrl=img://A",
            pool.snapshot("c1"))
    }

    run("scenario B") {
        val (pool, scheduler) = fixture()
        val token = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", token, 10)
        scheduler.queueResolution("itemA", "img://A")
        pool.recycle("c1")
        scheduler.advance(20)
        expect("scenario B",
            "c1 unbound",
            pool.snapshot("c1"))
    }

    run("scenario C") {
        val (pool, scheduler) = fixture()
        val tA = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", tA, 10)
        scheduler.queueResolution("itemA", "img://A")
        pool.bind("c1", "itemB", "Bob")
        scheduler.advance(20)
        expect("scenario C",
            "c1 item=itemB title=Bob imageUrl=NONE",
            pool.snapshot("c1"))
    }

    run("scenario D") {
        val (pool, scheduler) = fixture()
        val tA = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", tA, 10)
        scheduler.queueResolution("itemA", "img://A_old")
        pool.recycle("c1")
        pool.bind("c1", "itemA", "Alice")
        scheduler.advance(20)
        expect("scenario D",
            "c1 item=itemA title=Alice imageUrl=NONE",
            pool.snapshot("c1"))
    }

    run("scenario E") {
        val (pool, scheduler) = fixture()
        val tA = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", tA, 10)
        scheduler.queueResolution("itemA", "img://A_first")
        // Schedule a second fetch on the same binding before any tick.
        scheduler.schedule("c1", "itemA", tA, 12)
        scheduler.queueResolution("itemA", "img://A_second")
        scheduler.advance(20)
        // Only the first fetch should land. The cell settles on first image
        // and the second one becomes a no-op.
        expect("scenario E",
            "c1 item=itemA title=Alice imageUrl=img://A_first",
            pool.snapshot("c1"))
    }

    run("scenario F") {
        val (pool, scheduler) = fixture()
        val t1 = pool.bind("c1", "itemA", "Alice")
        scheduler.schedule("c1", "itemA", t1, 10)
        scheduler.queueResolution("itemA", "img://A")
        val t2 = pool.bind("c2", "itemB", "Bob")
        scheduler.schedule("c2", "itemB", t2, 10)
        scheduler.queueResolution("itemB", "img://B")
        scheduler.advance(20)
        expect("scenario F.1",
            "c1 item=itemA title=Alice imageUrl=img://A",
            pool.snapshot("c1"))
        expect("scenario F.2",
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
