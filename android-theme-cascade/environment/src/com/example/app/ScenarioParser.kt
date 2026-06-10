package com.example.app

class Cursor(private val text: String) {
    private var pos = 0

    private fun skipWs() { while (pos < text.length && text[pos].isWhitespace()) pos++ }

    fun expectObjectStart() { skipWs(); require(text[pos] == '{') { "Expected '{' at $pos" }; pos++ }
    fun tryObjectEnd(): Boolean { skipWs(); if (pos < text.length && text[pos] == '}') { pos++; return true }; return false }
    fun expectArrayStart() { skipWs(); require(text[pos] == '[') { "Expected '[' at $pos" }; pos++ }
    fun tryArrayEnd(): Boolean { skipWs(); if (pos < text.length && text[pos] == ']') { pos++; return true }; return false }
    fun expectColon() { skipWs(); require(text[pos] == ':') { "Expected ':' at $pos" }; pos++ }
    fun tryComma() { skipWs(); if (pos < text.length && text[pos] == ',') pos++ }

    fun readString(): String {
        skipWs()
        require(text[pos] == '"') { "Expected '\"' at $pos" }
        pos++
        val sb = StringBuilder()
        while (pos < text.length && text[pos] != '"') {
            if (text[pos] == '\\' && pos + 1 < text.length) {
                sb.append(when (text[pos + 1]) {
                    '"' -> '"'; '\\' -> '\\'; 'n' -> '\n'; 't' -> '\t'
                    else -> text[pos + 1]
                })
                pos += 2
            } else {
                sb.append(text[pos]); pos++
            }
        }
        pos++
        return sb.toString()
    }

    fun readNullableString(): String? {
        skipWs()
        if (text.startsWith("null", pos)) { pos += 4; return null }
        return readString()
    }

    fun skipValue() {
        skipWs()
        when (text[pos]) {
            '"' -> { readString() }
            '{' -> { expectObjectStart(); while (!tryObjectEnd()) { readString(); expectColon(); skipValue(); tryComma() } }
            '[' -> { expectArrayStart(); while (!tryArrayEnd()) { skipValue(); tryComma() } }
            else -> { while (pos < text.length && text[pos] !in ",}]") pos++ }
        }
    }
}

fun parseScenario(json: String): Scenario {
    val c = Cursor(json)
    c.expectObjectStart()
    var themes: List<ThemeSpec> = emptyList()
    var componentOverrides: List<ComponentOverrideSpec> = emptyList()
    var stateOverrides: List<StateOverrideSpec> = emptyList()
    var applies: List<ApplySpec> = emptyList()
    var activeTheme: String? = null
    var switches: List<String> = emptyList()
    var queries: List<QuerySpec> = emptyList()
    while (!c.tryObjectEnd()) {
        val key = c.readString(); c.expectColon()
        when (key) {
            "themes" -> themes = parseList(c) { parseTheme(it) }
            "componentOverrides" -> componentOverrides = parseList(c) { parseComponentOverride(it) }
            "stateOverrides" -> stateOverrides = parseList(c) { parseStateOverride(it) }
            "applies" -> applies = parseList(c) { parseApply(it) }
            "activeTheme" -> activeTheme = c.readNullableString()
            "switches" -> switches = parseList(c) { it.readString() }
            "queries" -> queries = parseList(c) { parseQuery(it) }
            else -> c.skipValue()
        }
        c.tryComma()
    }
    return Scenario(themes, componentOverrides, stateOverrides, applies, activeTheme, switches, queries)
}

private fun parseTheme(c: Cursor): ThemeSpec {
    c.expectObjectStart()
    var name = ""; var parent: String? = null; var tokens: Map<String, String> = emptyMap()
    while (!c.tryObjectEnd()) {
        val key = c.readString(); c.expectColon()
        when (key) {
            "name" -> name = c.readString()
            "parent" -> parent = c.readNullableString()
            "tokens" -> tokens = parseStringMap(c)
            else -> c.skipValue()
        }
        c.tryComma()
    }
    return ThemeSpec(name, parent, tokens)
}

private fun parseComponentOverride(c: Cursor): ComponentOverrideSpec {
    c.expectObjectStart()
    var component = ""; var token = ""; var value = ""
    while (!c.tryObjectEnd()) {
        val key = c.readString(); c.expectColon()
        when (key) {
            "component" -> component = c.readString()
            "token" -> token = c.readString()
            "value" -> value = c.readString()
            else -> c.skipValue()
        }
        c.tryComma()
    }
    return ComponentOverrideSpec(component, token, value)
}

private fun parseStateOverride(c: Cursor): StateOverrideSpec {
    c.expectObjectStart()
    var component = ""; var state = ""; var token = ""; var value = ""
    while (!c.tryObjectEnd()) {
        val key = c.readString(); c.expectColon()
        when (key) {
            "component" -> component = c.readString()
            "state" -> state = c.readString()
            "token" -> token = c.readString()
            "value" -> value = c.readString()
            else -> c.skipValue()
        }
        c.tryComma()
    }
    return StateOverrideSpec(component, state, token, value)
}

private fun parseApply(c: Cursor): ApplySpec {
    c.expectObjectStart()
    var component = ""; var theme = ""
    while (!c.tryObjectEnd()) {
        val key = c.readString(); c.expectColon()
        when (key) {
            "component" -> component = c.readString()
            "theme" -> theme = c.readString()
            else -> c.skipValue()
        }
        c.tryComma()
    }
    return ApplySpec(component, theme)
}

private fun parseQuery(c: Cursor): QuerySpec {
    c.expectObjectStart()
    var component = ""; var state = ""
    while (!c.tryObjectEnd()) {
        val key = c.readString(); c.expectColon()
        when (key) {
            "component" -> component = c.readString()
            "state" -> state = c.readString()
            else -> c.skipValue()
        }
        c.tryComma()
    }
    return QuerySpec(component, state)
}

private fun parseStringMap(c: Cursor): Map<String, String> {
    c.expectObjectStart()
    val out = mutableMapOf<String, String>()
    while (!c.tryObjectEnd()) {
        val key = c.readString(); c.expectColon()
        val value = c.readString()
        out[key] = value
        c.tryComma()
    }
    return out
}

private fun <T> parseList(c: Cursor, parseItem: (Cursor) -> T): List<T> {
    c.expectArrayStart()
    val out = mutableListOf<T>()
    while (!c.tryArrayEnd()) {
        out.add(parseItem(c))
        c.tryComma()
    }
    return out
}
