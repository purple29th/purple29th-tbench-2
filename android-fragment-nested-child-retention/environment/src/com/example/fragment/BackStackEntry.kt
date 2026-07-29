package com.example.fragment

data class CapturedFragmentState(
    val parent: String?,
    val hidden: Boolean,
    val lifecycle: Lifecycle,
    val viewModel: Map<String, String>,
    val savedState: Map<String, String>,
    val children: Set<String>
)

data class BackStackEntry(
    val name: String?,
    val ops: List<TransactionOp>,
    val replacedFragments: Map<String, List<Fragment>>,
    val replacedChildStates: Map<String, Map<String, CapturedFragmentState>>, // container -> fragmentName -> full subtree states
    val replacedRootStates: Map<String, CapturedFragmentState>,
    val hiddenSnapshot: Map<String, Boolean>
)
