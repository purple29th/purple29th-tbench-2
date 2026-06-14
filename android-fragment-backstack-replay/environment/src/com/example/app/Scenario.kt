package com.example.app

sealed class Op {
    data class Begin(val txnId: String) : Op()
    data class Add(val txnId: String, val container: String, val fragment: String) : Op()
    data class Replace(val txnId: String, val container: String, val fragment: String) : Op()
    data class Remove(val txnId: String, val fragment: String) : Op()
    data class AddToBackStack(val txnId: String, val name: String?) : Op()
    data class Commit(val txnId: String) : Op()
    data class Pop(val name: String?) : Op()
    object Rotate : Op()
    object Query : Op()
}

data class Scenario(val ops: List<Op>)
