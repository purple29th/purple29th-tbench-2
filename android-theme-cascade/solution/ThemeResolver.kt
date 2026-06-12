package com.example.theme

import com.example.coreui.Component

class ThemeResolver(
    private val registry: ThemeRegistry
) {
    private var activeTheme: String? = null
    private val components = mutableMapOf<String, Component>()

    fun setActiveTheme(name: String) {
        require(registry.has(name)) { "Unknown theme: $name" }
        activeTheme = name
    }

    fun apply(component: Component, themeName: String) {
        require(registry.has(themeName)) { "Unknown theme: $themeName" }
        component.bindTo(themeName)
        components[component.name] = component
    }

    fun trackComponent(component: Component) {
        components[component.name] = component
    }

    fun switchActiveTheme(name: String) {
        require(registry.has(name)) { "Unknown theme: $name" }
        activeTheme = name
    }

    fun resolve(component: Component, state: String): Map<String, String> {
        val themeName = component.explicitTheme ?: activeTheme
            ?: throw IllegalStateException("No theme bound for ${component.name}")
        val theme = registry.get(themeName)
        val merged = TokenMap()
        merged.mergeFrom(theme.parentSnapshot())
        merged.mergeFrom(theme.ownTokens())
        merged.mergeFrom(component.componentOverrides())
        component.stateOverridesFor(state)?.let { merged.mergeFrom(it) }
        return merged.snapshot()
    }
}
