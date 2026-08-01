package com.example.fragment

sealed class TransactionOp {
    data class Add(val container: String, val fragment: Fragment) : TransactionOp()
    data class Replace(val container: String, val fragment: Fragment) : TransactionOp()
    data class Remove(val fragment: Fragment) : TransactionOp()
    data class SetListener(val fragment: String, val key: String) : TransactionOp()
    data class ClearListener(val fragment: String, val key: String) : TransactionOp()
    data class SetResult(val target: String, val key: String, val value: String) : TransactionOp()
}

class Transaction(val id: String) {
    private val ops = mutableListOf<TransactionOp>()
    var addToBackStack: Boolean = false
    var backStackName: String? = null

    fun addOp(op: TransactionOp) { ops.add(op) }
    fun operations(): List<TransactionOp> = ops.toList()
    fun markBackStack(name: String?) { addToBackStack = true; backStackName = name }
}
