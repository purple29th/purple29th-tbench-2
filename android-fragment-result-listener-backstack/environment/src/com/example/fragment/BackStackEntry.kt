package com.example.fragment

data class FragmentSnapshot(
    val name: String,
    val container: String?,
    val listeners: Set<String>,
    val pending: Map<String, String>,
    val delivered: Map<String, String>
)

data class BackStackEntry(
    val name: String?,
    val ops: List<TransactionOp>,
    val replaced: Map<String, List<Fragment>>, // container -> previous fragments
    val replacedStates: Map<String, FragmentSnapshot> // fragment name -> snapshot
)
