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
        val replaced = applyOpsAndCaptureReplaced(txn.operations())
        if (txn.addToBackStack) {
            backStack.add(BackStackEntry(txn.backStackName, txn.operations(), replaced))
        }
    }

    fun pop(name: String?) {
        if (backStack.isEmpty()) return
        if (name == null) {
            // Pop only the topmost entry, but if the topmost is a named entry,
            // do nothing — anonymous POP cannot cross a named-entry boundary.
            val top = backStack.last()
            if (top.name != null) return
            reverseEntry(backStack.removeAt(backStack.size - 1))
            return
        }
        val index = backStack.indexOfLast { it.name == name }
        if (index < 0) return
        while (backStack.size > index) {
            reverseEntry(backStack.removeAt(backStack.size - 1))
        }
    }

    fun rotate() {
        for (container in containers.values) container.clear()
        val saved = backStack.toList()
        backStack.clear()
        for (entry in saved) {
            TransactionReplay.replayInto(containers, entry.ops)
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

    private fun applyOpsAndCaptureReplaced(ops: List<TransactionOp>): Map<String, List<Fragment>> {
        val replaced = mutableMapOf<String, List<Fragment>>()
        for (op in ops) {
            when (op) {
                is TransactionOp.Add -> {
                    containers.getOrPut(op.container) { Container(op.container) }.add(op.fragment)
                }
                is TransactionOp.Replace -> {
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val previous = container.replace(op.fragment)
                    if (previous.isNotEmpty()) replaced[op.container] = previous
                }
                is TransactionOp.Remove -> {
                    for (container in containers.values) container.remove(op.fragment)
                }
            }
        }
        return replaced
    }

    private fun reverseEntry(entry: BackStackEntry) {
        for (op in entry.ops.reversed()) {
            when (op) {
                is TransactionOp.Add -> {
                    containers[op.container]?.remove(op.fragment)
                }
                is TransactionOp.Replace -> {
                    val container = containers[op.container] ?: continue
                    container.remove(op.fragment)
                    val previous = entry.replacedFragments[op.container] ?: continue
                    for (fragment in previous) container.add(fragment)
                }
                is TransactionOp.Remove -> {}
            }
        }
    }
}
