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

    // BUG: rebinds every component to the new active theme, including ones with explicit apply().
    fun switchActiveTheme(name: String) {
        require(registry.has(name)) { "Unknown theme: $name" }
        activeTheme = name
        for (component in components.values) {
            component.bindTo(name)
        }
    }

    fun resolve(component: Component, state: String): Map<String, String> {
        val themeName = component.explicitTheme ?: activeTheme
            ?: throw IllegalStateException("No theme bound for ${component.name} and no active theme set")
        val theme = registry.get(themeName)
        val merged = TokenMap()

        // BUG: cascade order is inverted — applies state first, then component, then theme on top.
        component.stateOverridesFor(state)?.let { merged.mergeFrom(it) }
        merged.mergeFrom(component.componentOverrides())
        for (ancestor in theme.parentChain()) {
            merged.mergeFrom(ancestor.ownTokens())
        }

        // BUG: applies every state override regardless of requested state.
        for (s in listOf("default", "pressed", "focused", "disabled")) {
            component.stateOverridesFor(s)?.let { merged.mergeFrom(it) }
        }

        return merged.snapshot()
    }
}
