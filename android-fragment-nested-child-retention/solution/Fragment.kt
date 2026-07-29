package com.example.fragment

data class Fragment(val name: String)

enum class Lifecycle {
    INITIALIZED, CREATED, VIEW_CREATED, STARTED, RESUMED
}

fun lifecycleOrder(l: Lifecycle): Int = when (l) {
    Lifecycle.INITIALIZED -> 0
    Lifecycle.CREATED -> 1
    Lifecycle.VIEW_CREATED -> 2
    Lifecycle.STARTED -> 3
    Lifecycle.RESUMED -> 4
}

fun minLifecycle(a: Lifecycle, b: Lifecycle): Lifecycle =
    if (lifecycleOrder(a) <= lifecycleOrder(b)) a else b

data class FragmentState(
    val fragment: Fragment,
    var parent: String? = null,
    var hidden: Boolean = false,
    var detached: Boolean = false,
    var lifecycle: Lifecycle = Lifecycle.RESUMED,
    var maxLifecycle: Lifecycle = Lifecycle.RESUMED,
    var lastContainer: String? = null,
    val viewModel: MutableMap<String, String> = mutableMapOf(),
    val savedState: MutableMap<String, String> = mutableMapOf(),
    val children: MutableSet<String> = mutableSetOf()
)
