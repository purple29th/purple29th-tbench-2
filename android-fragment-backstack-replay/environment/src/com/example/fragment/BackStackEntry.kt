package com.example.fragment

data class BackStackEntry(
    val name: String?,
    val ops: List<TransactionOp>,
    val replacedFragments: Map<String, List<Fragment>>
)
