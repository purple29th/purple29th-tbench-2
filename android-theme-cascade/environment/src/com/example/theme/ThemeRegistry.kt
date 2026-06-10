package com.example.theme

class ThemeRegistry {
    private val themes = mutableMapOf<String, Theme>()
    fun register(theme: Theme) { themes[theme.name] = theme }
    fun get(name: String): Theme = themes[name] ?: throw IllegalArgumentException("Unknown theme: $name")
    fun has(name: String): Boolean = themes.containsKey(name)
}
