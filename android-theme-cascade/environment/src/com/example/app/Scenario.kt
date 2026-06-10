package com.example.app

data class ThemeSpec(val name: String, val parent: String?, val tokens: Map<String, String>)
data class ComponentOverrideSpec(val component: String, val token: String, val value: String)
data class StateOverrideSpec(val component: String, val state: String, val token: String, val value: String)
data class ApplySpec(val component: String, val theme: String)
data class QuerySpec(val component: String, val state: String)

data class Scenario(
    val themes: List<ThemeSpec>,
    val componentOverrides: List<ComponentOverrideSpec>,
    val stateOverrides: List<StateOverrideSpec>,
    val applies: List<ApplySpec>,
    val activeTheme: String?,
    val switches: List<String>,
    val queries: List<QuerySpec>
)
