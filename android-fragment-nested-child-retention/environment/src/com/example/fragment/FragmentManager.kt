package com.example.fragment

class FragmentManager {
    private val containers = mutableMapOf<String, Container>()
    private val fragmentStates = mutableMapOf<String, FragmentState>()
    private val openTransactions = mutableMapOf<String, Transaction>()
    private val backStack = mutableListOf<BackStackEntry>()

    fun begin(txnId: String) { openTransactions[txnId] = Transaction(txnId) }

    fun add(txnId: String, container: String, fragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.Add(container, Fragment(fragment)))
    }

    fun addChild(txnId: String, parent: String, childContainer: String, childFragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.AddChild(parent, childContainer, Fragment(childFragment)))
    }

    fun replace(txnId: String, container: String, fragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.Replace(container, Fragment(fragment)))
    }

    fun remove(txnId: String, fragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.Remove(Fragment(fragment)))
    }

    fun hide(txnId: String, fragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.Hide(Fragment(fragment)))
    }

    fun show(txnId: String, fragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.Show(Fragment(fragment)))
    }

    fun save(fragment: String, key: String, value: String) {
        fragmentStates.getOrPut(fragment) { FragmentState(Fragment(fragment)) }.savedState[key] = value
    }

    fun putViewModel(fragment: String, key: String, value: String) {
        fragmentStates.getOrPut(fragment) { FragmentState(Fragment(fragment)) }.viewModel[key] = value
    }

    fun addToBackStack(txnId: String, name: String?) {
        openTransactions[txnId]?.markBackStack(name)
    }

    fun commit(txnId: String) {
        val txn = openTransactions.remove(txnId) ?: return
        val replaced = mutableMapOf<String, List<Fragment>>()
        for (op in txn.operations()) {
            when (op) {
                is TransactionOp.Replace -> {
                    val container = containers[op.container]
                    if (container != null) {
                        replaced[op.container] = container.snapshot()
                    }
                }
                else -> {}
            }
        }
        applyOps(txn.operations())
        if (txn.addToBackStack) {
            backStack.add(
                BackStackEntry(
                    txn.backStackName,
                    txn.operations(),
                    replaced,
                    emptyMap(),
                    emptyMap(),
                    emptyMap()
                )
            )
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
        fragmentStates.clear()
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
        for ((name, state) in fragmentStates.toSortedMap()) {
            val parent = state.parent ?: "NONE"
            val vm = state.viewModel.toSortedMap().entries.joinToString(", ") { "${it.key}=${it.value}" }
            val ss = state.savedState.toSortedMap().entries.joinToString(", ") { "${it.key}=${it.value}" }
            val childs = state.children.sorted().joinToString(", ")
            builder.append("fragment=").append(name)
                .append(" parent=").append(parent)
                .append(" hidden=").append(state.hidden)
                .append(" lifecycle=").append(state.lifecycle)
                .append(" viewModel={").append(vm).append("}")
                .append(" savedState={").append(ss).append("}")
                .append(" children=[").append(childs).append("]\n")
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
                    val fragState = fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                    fragState.parent = null
                    fragState.lifecycle = if (fragState.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                    container.add(op.fragment)
                }
                is TransactionOp.AddChild -> {
                    allContainersEverUsed.add(op.childContainer)
                    val parentState = fragmentStates[op.parentFragment]
                    val childState = fragmentStates.getOrPut(op.childFragment.name) { FragmentState(op.childFragment) }
                    childState.parent = op.parentFragment
                    childState.lifecycle = if (childState.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                    if (parentState != null) {
                        parentState.children.add(op.childFragment.name)
                    }
                    val container = containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    container.add(op.childFragment)
                }
                is TransactionOp.Replace -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    container.replace(op.fragment)
                    val newState = fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                    newState.parent = null
                    newState.lifecycle = if (newState.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                }
                is TransactionOp.Remove -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    for (c in containers.values) {
                        c.remove(op.fragment)
                    }
                    if (state.parent != null) {
                        fragmentStates[state.parent]?.children?.remove(op.fragment.name)
                    }
                    fragmentStates.remove(op.fragment.name)
                }
                is TransactionOp.Hide -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.hidden = true
                }
                is TransactionOp.Show -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.hidden = false
                    state.lifecycle = Lifecycle.RESUMED
                }
            }
        }
    }

    private fun reverseEntry(entry: BackStackEntry) {
        for (op in entry.ops.reversed()) {
            when (op) {
                is TransactionOp.Add -> {
                    containers[op.container]?.remove(op.fragment)
                    val st = fragmentStates[op.fragment.name]
                    if (st != null) {
                        fragmentStates.remove(op.fragment.name)
                    }
                }
                is TransactionOp.AddChild -> {
                    containers[op.childContainer]?.remove(op.childFragment)
                    fragmentStates[op.parentFragment]?.children?.remove(op.childFragment.name)
                    fragmentStates.remove(op.childFragment.name)
                }
                is TransactionOp.Replace -> {
                    val container = containers[op.container] ?: continue
                    container.remove(op.fragment)
                    fragmentStates.remove(op.fragment.name)
                    val previous = entry.replacedFragments[op.container] ?: emptyList()
                    for (frag in previous) {
                        container.add(frag)
                        fragmentStates.getOrPut(frag.name) { FragmentState(frag) }
                    }
                }
                is TransactionOp.Remove -> {}
                is TransactionOp.Hide -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.hidden = false
                        it.lifecycle = Lifecycle.RESUMED
                    }
                }
                is TransactionOp.Show -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.hidden = true
                        it.lifecycle = Lifecycle.STARTED
                    }
                }
            }
        }
    }
}
