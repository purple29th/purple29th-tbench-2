package com.example.fragment

data class Fragment(val name: String)

enum class Lifecycle {
    INITIALIZED, CREATED, VIEW_CREATED, STARTED, RESUMED
}

data class FragmentState(
    val fragment: Fragment,
    var parent: String? = null,
    var hidden: Boolean = false,
    var lifecycle: Lifecycle = Lifecycle.RESUMED,
    val viewModel: MutableMap<String, String> = mutableMapOf(),
    val savedState: MutableMap<String, String> = mutableMapOf(),
    val children: MutableSet<String> = mutableSetOf()
)
