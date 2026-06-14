package com.example.fragment

class FragmentManager {
    private val containers = mutableMapOf<String, Container>()
    private val openTransactions = mutableMapOf<String, Transaction>()
    private val backStack = mutableListOf<BackStackEntry>()

    fun begin(txnId: String) { openTransactions[txnId] = Transaction(txnId) }

    fun add(txnId: String, container: String, fragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.Add(container, Fragment(fragment)))
    }

    fun replace(txnId: String, container: String, fragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.Replace(container, Fragment(fragment)))
    }

    fun remove(txnId: String, fragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.Remove(Fragment(fragment)))
    }

    fun addToBackStack(txnId: String, name: String?) {
        openTransactions[txnId]?.markBackStack(name)
    }

    fun commit(txnId: String) {
        val txn = openTransactions.remove(txnId) ?: return
        applyOps(txn.operations())
        if (txn.addToBackStack) {
            backStack.add(BackStackEntry(txn.backStackName, txn.operations(), emptyMap()))
        }
    }

    fun pop(name: String?) {
        if (backStack.isEmpty()) return
        if (name == null) {
            reverseEntry(backStack.removeAt(backStack.size - 1))
            return
        }
        val index = backStack.indexOfFirst { it.name == name }
        if (index < 0) {
            while (backStack.isNotEmpty()) {
                reverseEntry(backStack.removeAt(backStack.size - 1))
            }
            return
        }
        while (backStack.size > index + 1) {
            reverseEntry(backStack.removeAt(backStack.size - 1))
        }
    }

    fun rotate() {
        for (container in containers.values) container.clear()
        val saved = backStack.toList()
        backStack.clear()
        for (entry in saved) {
            applyOps(entry.ops)
            backStack.add(entry)
        }
    }

    fun snapshot(): String {
        val builder = StringBuilder()
        for ((id, container) in containers.toSortedMap()) {
            val frags = container.snapshot().joinToString(", ") { it.name }
            builder.append("container=").append(id).append(" fragments=[").append(frags).append("]\n")
        }
        val entries = backStack.joinToString(", ") { it.name ?: "anon" }
        builder.append("backstack=[").append(entries).append("]\n")
        return builder.toString()
    }

    private fun applyOps(ops: List<TransactionOp>) {
        for (op in ops) {
            when (op) {
                is TransactionOp.Add -> {
                    containers.getOrPut(op.container) { Container(op.container) }.add(op.fragment)
                }
                is TransactionOp.Replace -> {
                    containers.getOrPut(op.container) { Container(op.container) }.replace(op.fragment)
                }
                is TransactionOp.Remove -> {
                    for (container in containers.values) container.remove(op.fragment)
                }
            }
        }
    }

    private fun reverseEntry(entry: BackStackEntry) {
        for (op in entry.ops.reversed()) {
            when (op) {
                is TransactionOp.Add -> {
                    containers[op.container]?.remove(op.fragment)
                }
                is TransactionOp.Replace -> {
                    containers[op.container]?.remove(op.fragment)
                }
                is TransactionOp.Remove -> {}
            }
        }
    }
}
