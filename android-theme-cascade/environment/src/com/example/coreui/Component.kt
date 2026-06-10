package com.example.coreui

import com.example.theme.TokenMap

class Component(val name: String) {
    private val componentOverrides = TokenMap()
    private val stateOverrides = mutableMapOf<String, TokenMap>()
    var explicitTheme: String? = null
        private set

    fun setComponentOverride(key: String, value: String) {
        componentOverrides.set(key, value)
    }

    fun setStateOverride(state: String, key: String, value: String) {
        stateOverrides.getOrPut(state) { TokenMap() }.set(key, value)
    }

    fun bindTo(themeName: String) { explicitTheme = themeName }

    fun componentOverrides(): TokenMap = componentOverrides
    fun stateOverridesFor(state: String): TokenMap? = stateOverrides[state]
}
