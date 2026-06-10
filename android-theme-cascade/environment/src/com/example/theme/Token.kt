package com.example.theme

class TokenMap(private val values: MutableMap<String, String> = mutableMapOf()) {
    fun set(key: String, value: String) { values[key] = value }
    fun get(key: String): String? = values[key]
    fun keys(): Set<String> = values.keys
    fun snapshot(): Map<String, String> = values.toSortedMap()
    fun mergeFrom(other: TokenMap) { values.putAll(other.values.toMap()) }
    fun internalValues(): Map<String, String> = values.toMap()
}
