package com.example.fragment

class FragmentManager {
    private val containers = mutableMapOf<String, Container>()
    private val fragments = mutableMapOf<String, FragmentSnapshotMutable>()
    private val openTransactions = mutableMapOf<String, Transaction>()
    private val backStack = mutableListOf<BackStackEntry>()

    private data class FragmentSnapshotMutable(
        var name: String,
        var container: String?,
        val listeners: MutableSet<String> = mutableSetOf(),
        val pending: MutableMap<String, String> = mutableMapOf(),
        val delivered: MutableMap<String, String> = mutableMapOf()
    ) {
        fun toSnapshot() = FragmentSnapshot(name, container, listeners.toSet(), pending.toMap(), delivered.toMap())
    }

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
    fun setResultListener(txnId: String, fragment: String, key: String) {
        openTransactions[txnId]?.addOp(TransactionOp.SetListener(fragment, key))
    }
    fun clearResultListener(txnId: String, fragment: String, key: String) {
        openTransactions[txnId]?.addOp(TransactionOp.ClearListener(fragment, key))
    }
    fun setResult(txnId: String, target: String, key: String, value: String) {
        openTransactions[txnId]?.addOp(TransactionOp.SetResult(target, key, value))
    }
    fun addToBackStack(txnId: String, name: String?) {
        openTransactions[txnId]?.markBackStack(name)
    }
    fun commit(txnId: String) {
        val txn = openTransactions.remove(txnId) ?: return
        val replacedContainers = mutableMapOf<String, List<Fragment>>()
        val replacedStates = mutableMapOf<String, FragmentSnapshot>()
        for (op in txn.operations()) {
            if (op is TransactionOp.Replace) {
                val container = containers[op.container]
                if (container != null) {
                    replacedContainers[op.container] = container.snapshot()
                    for (frag in container.snapshot()) {
                        fragments[frag.name]?.let { fs ->
                            replacedStates[frag.name] = fs.toSnapshot()
                        }
                    }
                }
            }
        }
        applyOps(txn.operations())
        if (txn.addToBackStack) {
            backStack.add(BackStackEntry(txn.backStackName, txn.operations(), replacedContainers, replacedStates))
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
        fragments.clear()
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
            val frags = container.snapshot().map { it.name }.sorted()
            if (frags.isEmpty() && !allContainersEverUsed.contains(id)) continue
            builder.append("container=").append(id).append(" fragments=[").append(frags.joinToString(", ")).append("]\n")
        }
        for ((name, state) in fragments.toSortedMap()) {
            val listeners = state.listeners.sorted().joinToString(", ")
            val pending = state.pending.toSortedMap().entries.joinToString(", ") { "${it.key}=${it.value}" }
            val delivered = state.delivered.toSortedMap().entries.joinToString(", ") { "${it.key}=${it.value}" }
            builder.append("fragment=").append(name)
                .append(" listeners=[").append(listeners).append("]")
                .append(" pending={").append(pending).append("}")
                .append(" delivered={").append(delivered).append("}\n")
        }
        val entries = backStack.joinToString(", ") { it.name ?: "anon" }
        builder.append("backstack=[").append(entries).append("]\n")
        return builder.toString()
    }
    private val allContainersEverUsed = mutableSetOf<String>()
    private fun applyOps(ops: List<TransactionOp>) {
        for (op in ops) {
            when (op) {
                is TransactionOp.Add -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val fs = fragments.getOrPut(op.fragment.name) { FragmentSnapshotMutable(op.fragment.name, null) }
                    fs.container = op.container
                    container.add(op.fragment)
                }
                is TransactionOp.Replace -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    for (old in container.snapshot()) {
                        containers[op.container]?.remove(old)
                    }
                    container.replace(op.fragment)
                    val fs = fragments.getOrPut(op.fragment.name) { FragmentSnapshotMutable(op.fragment.name, null) }
                    fs.container = op.container
                }
                is TransactionOp.Remove -> {
                    for (c in containers.values) c.remove(op.fragment)
                    fragments.remove(op.fragment.name)
                }
                is TransactionOp.SetListener -> {
                    val fs = fragments[op.fragment] ?: continue
                    fs.listeners.add(op.key)
                }
                is TransactionOp.ClearListener -> {
                    val fs = fragments[op.fragment] ?: continue
                    fs.listeners.remove(op.key)
                }
                is TransactionOp.SetResult -> {
                    val fs = fragments[op.target] ?: continue
                    if (fs.listeners.contains(op.key)) {
                        fs.delivered[op.key] = op.value
                    } else {
                        fs.pending[op.key] = op.value
                    }
                }
            }
        }
    }
    private fun reverseEntry(entry: BackStackEntry) {
        for (op in entry.ops.reversed()) {
            when (op) {
                is TransactionOp.Add -> {
                    containers[op.container]?.remove(op.fragment)
                    fragments.remove(op.fragment.name)
                }
                is TransactionOp.Replace -> {
                    val container = containers[op.container] ?: continue
                    container.remove(op.fragment)
                    fragments.remove(op.fragment.name)
                    val previous = entry.replaced[op.container] ?: emptyList()
                    for (frag in previous) {
                        container.add(frag)
                        val snap = entry.replacedStates[frag.name]
                        if (snap != null) {
                            fragments[frag.name] = FragmentSnapshotMutable(
                                snap.name, snap.container, snap.listeners.toMutableSet(), snap.pending.toMutableMap(), snap.delivered.toMutableMap()
                            )
                        } else {
                            fragments.getOrPut(frag.name) { FragmentSnapshotMutable(frag.name, op.container) }
                        }
                    }
                }
                is TransactionOp.Remove -> {}
                is TransactionOp.SetListener -> {
                    fragments[op.fragment]?.listeners?.remove(op.key)
                }
                is TransactionOp.ClearListener -> {}
                is TransactionOp.SetResult -> {
                    val fs = fragments[op.target] ?: continue
                    fs.delivered.remove(op.key)
                    fs.pending.remove(op.key)
                }
            }
        }
    }
}
