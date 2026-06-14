package com.example.fragment

sealed class TransactionOp {
    data class Add(val container: String, val fragment: Fragment) : TransactionOp()
    data class Replace(val container: String, val fragment: Fragment) : TransactionOp()
    data class Remove(val fragment: Fragment) : TransactionOp()
}

class Transaction(val id: String) {
    private val ops = mutableListOf<TransactionOp>()
    var addToBackStack: Boolean = false
        private set
    var backStackName: String? = null
        private set

    fun addOp(op: TransactionOp) { ops.add(op) }

    fun markBackStack(name: String?) {
        addToBackStack = true
        backStackName = name
    }

    fun operations(): List<TransactionOp> = ops.toList()
}
