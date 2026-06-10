package com.example.theme.test

import com.example.coreui.Component
import com.example.theme.Theme
import com.example.theme.ThemeRegistry
import com.example.theme.ThemeResolver

// Visible contract describing the expected resolver behavior.
// Run via: bash /app/src/run-contract.sh
// Each function returns (testName, passed). Failures print actual-vs-expected.

private val results = mutableListOf<Pair<String, String>>()

private fun expect(name: String, expected: Map<String, String>, actual: Map<String, String>) {
    if (expected == actual) {
        results.add(name to "PASS")
    } else {
        results.add(name to "FAIL\n  expected: $expected\n  actual:   $actual")
    }
}

private fun fixture(): Pair<ThemeRegistry, ThemeResolver> {
    val registry = ThemeRegistry()
    val base = Theme("Base", null).apply {
        setToken("colorPrimary", "#000000")
        setToken("colorBackground", "#FFFFFF")
    }
    val dark = Theme("Dark", base).apply { setToken("colorPrimary", "#1A1A1A") }
    val light = Theme("Light", base).apply {
        setToken("colorPrimary", "#EFEFEF")
        setToken("colorBackground", "#FAFAFA")
    }
    registry.register(base); registry.register(dark); registry.register(light)
    val resolver = ThemeResolver(registry)
    resolver.setActiveTheme("Dark")
    return registry to resolver
}

fun main() {
    run("child theme overrides parent") {
        val (_, r) = fixture()
        val b = Component("Button"); r.trackComponent(b)
        expect("child theme overrides parent",
            mapOf("colorPrimary" to "#1A1A1A", "colorBackground" to "#FFFFFF"),
            r.resolve(b, "default"))
    }

    run("component override beats theme") {
        val (_, r) = fixture()
        val b = Component("Button").apply { setComponentOverride("colorBackground", "#222222") }
        r.trackComponent(b)
        expect("component override beats theme",
            mapOf("colorPrimary" to "#1A1A1A", "colorBackground" to "#222222"),
            r.resolve(b, "default"))
    }

    run("state override applies only in matching state") {
        val (_, r) = fixture()
        val b = Component("Button").apply { setStateOverride("pressed", "colorBackground", "#444444") }
        r.trackComponent(b)
        expect("default state ignores pressed override",
            mapOf("colorPrimary" to "#1A1A1A", "colorBackground" to "#FFFFFF"),
            r.resolve(b, "default"))
        expect("pressed state uses pressed override",
            mapOf("colorPrimary" to "#1A1A1A", "colorBackground" to "#444444"),
            r.resolve(b, "pressed"))
    }

    run("explicit apply survives switchActiveTheme") {
        val (_, r) = fixture()
        val b = Component("Button"); r.apply(b, "Dark")
        r.switchActiveTheme("Light")
        expect("explicit apply survives switchActiveTheme",
            mapOf("colorPrimary" to "#1A1A1A", "colorBackground" to "#FFFFFF"),
            r.resolve(b, "default"))
    }

    run("unbound component follows switchActiveTheme") {
        val (_, r) = fixture()
        val c = Component("Card"); r.trackComponent(c)
        r.switchActiveTheme("Light")
        expect("unbound component follows switchActiveTheme",
            mapOf("colorPrimary" to "#EFEFEF", "colorBackground" to "#FAFAFA"),
            r.resolve(c, "default"))
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
    if (allPass) println("\nAll contract tests pass.") else println("\nContract failures above.")
}

private fun run(name: String, block: () -> Unit) {
    try { block() } catch (e: Throwable) { results.add(name to "FAIL\n  exception: ${e.message}") }
}
