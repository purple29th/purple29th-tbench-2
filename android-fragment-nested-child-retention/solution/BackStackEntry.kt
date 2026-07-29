package com.example.fragment

data class CapturedFragmentState(
    val parent: String?,
    val hidden: Boolean,
    val detached: Boolean,
    val lifecycle: Lifecycle,
    val maxLifecycle: Lifecycle,
    val lastContainer: String?,
    val viewModel: Map<String, String>,
    val savedState: Map<String, String>,
    val children: Set<String>
)

data class BackStackEntry(
    val name: String?,
    val ops: List<TransactionOp>,
    val replacedFragments: Map<String, List<Fragment>>,
    val replacedChildStates: Map<String, Map<String, CapturedFragmentState>>,
    val replacedRootStates: Map<String, CapturedFragmentState>,
    val hiddenSnapshot: Map<String, Boolean>,
    val maxSnapshot: Map<String, Lifecycle> = emptyMap(),
    val detachedSnapshot: Map<String, Boolean> = emptyMap(),
    val containerMap: Map<String, String> = emptyMap(),
    val allStates: Map<String, CapturedFragmentState> = emptyMap()
)
