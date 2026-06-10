package com.example.app

import com.example.coreui.Component
import com.example.theme.Theme
import com.example.theme.ThemeRegistry
import com.example.theme.ThemeResolver
import java.io.File

fun main() {
    val scenario = parseScenario(File("/app/scenario.json").readText())
    val output = runScenario(scenario)
    File("/app/output.json").writeText(output)
}

fun runScenario(scenario: Scenario): String {
    val registry = ThemeRegistry()
    for (themeSpec in scenario.themes) {
        val parent = themeSpec.parent?.let { registry.get(it) }
        val theme = Theme(themeSpec.name, parent)
        for ((key, value) in themeSpec.tokens) theme.setToken(key, value)
        registry.register(theme)
    }

    val resolver = ThemeResolver(registry)
    val components = mutableMapOf<String, Component>()

    for (spec in scenario.componentOverrides) {
        components.getOrPut(spec.component) { Component(spec.component) }
            .setComponentOverride(spec.token, spec.value)
    }
    for (spec in scenario.stateOverrides) {
        components.getOrPut(spec.component) { Component(spec.component) }
            .setStateOverride(spec.state, spec.token, spec.value)
    }
    for (component in components.values) resolver.trackComponent(component)

    scenario.activeTheme?.let { resolver.setActiveTheme(it) }

    for (spec in scenario.applies) {
        val component = components.getOrPut(spec.component) { Component(spec.component) }
        resolver.apply(component, spec.theme)
    }

    for (themeName in scenario.switches) resolver.switchActiveTheme(themeName)

    val resultsBuilder = StringBuilder()
    resultsBuilder.append("{\n  \"results\": [\n")
    for ((index, q) in scenario.queries.withIndex()) {
        val component = components.getOrPut(q.component) { Component(q.component) }
        resolver.trackComponent(component)
        val tokens = resolver.resolve(component, q.state)
        resultsBuilder.append("    {\"component\": \"")
        resultsBuilder.append(escape(q.component))
        resultsBuilder.append("\", \"state\": \"")
        resultsBuilder.append(escape(q.state))
        resultsBuilder.append("\", \"tokens\": {")
        val tokenEntries = tokens.entries.joinToString(", ") {
            "\"${escape(it.key)}\": \"${escape(it.value)}\""
        }
        resultsBuilder.append(tokenEntries)
        resultsBuilder.append("}}")
        if (index < scenario.queries.size - 1) resultsBuilder.append(",")
        resultsBuilder.append("\n")
    }
    resultsBuilder.append("  ]\n}\n")
    return resultsBuilder.toString()
}

private fun escape(value: String): String =
    value.replace("\\", "\\\\").replace("\"", "\\\"")
