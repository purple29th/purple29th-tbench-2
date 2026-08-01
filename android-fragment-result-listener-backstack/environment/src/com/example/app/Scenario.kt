package com.example.app

sealed class Op {
    data class Begin(val txnId: String) : Op()
    data class Add(val txnId: String, val container: String, val fragment: String) : Op()
    data class Replace(val txnId: String, val container: String, val fragment: String) : Op()
    data class Remove(val txnId: String, val fragment: String) : Op()
    data class SetListener(val txnId: String, val fragment: String, val key: String) : Op()
    data class ClearListener(val txnId: String, val fragment: String, val key: String) : Op()
    data class SetResult(val txnId: String, val target: String, val key: String, val value: String) : Op()
    data class AddToBackStack(val txnId: String, val name: String?) : Op()
    data class Commit(val txnId: String) : Op()
    data class Pop(val name: String?) : Op()
    object Rotate : Op()
    object Query : Op()
}

data class Scenario(val ops: List<Op>)
