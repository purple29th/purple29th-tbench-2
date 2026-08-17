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
    fun detach(txnId: String, fragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.Detach(Fragment(fragment)))
    }
    fun attach(txnId: String, fragment: String) {
        openTransactions[txnId]?.addOp(TransactionOp.Attach(Fragment(fragment)))
    }
    fun setMax(txnId: String, fragment: String, maxState: String) {
        val lc = try { Lifecycle.valueOf(maxState) } catch (e: Exception) { Lifecycle.RESUMED }
        openTransactions[txnId]?.addOp(TransactionOp.SetMax(Fragment(fragment), lc))
    }
    fun save(fragment: String, key: String, value: String) {
        fragmentStates.getOrPut(fragment) { FragmentState(Fragment(fragment)) }.savedState[key] = value
    }
    fun putViewModel(fragment: String, key: String, value: String) {
        fragmentStates.getOrPut(fragment) { FragmentState(Fragment(fragment)) }.viewModel[key] = value
    }
    fun putBinding(fragment: String, key: String, value: String) {
        fragmentStates.getOrPut(fragment) { FragmentState(Fragment(fragment)) }.binding[key] = value
    }
    fun addToBackStack(txnId: String, name: String?) {
        openTransactions[txnId]?.markBackStack(name)
    }
    fun commit(txnId: String) {
        val txn = openTransactions.remove(txnId) ?: return
        val replaced = mutableMapOf<String, List<Fragment>>()
        val replacedStates = mutableMapOf<String, FragmentState>()
        for (op in txn.operations()) {
            if (op is TransactionOp.Replace) {
                val container = containers[op.container]
                if (container != null) {
                    replaced[op.container] = container.snapshot()
                    for (frag in container.snapshot()) {
                        fragmentStates[frag.name]?.let { st ->
                            replacedStates[frag.name] = st.copy(
                                viewModel = st.viewModel.toMutableMap(),
                                savedState = st.savedState.toMutableMap(),
                                binding = st.binding.toMutableMap(),
                                children = st.children.toMutableSet()
                            )
                        }
                    }
                }
            }
            if (op is TransactionOp.Remove) {
                fragmentStates[op.fragment.name]?.let { st ->
                    replacedStates[op.fragment.name] = st.copy(
                        viewModel = st.viewModel.toMutableMap(),
                        savedState = st.savedState.toMutableMap(),
                        binding = st.binding.toMutableMap(),
                        children = st.children.toMutableSet()
                    )
                    st.lastContainer?.let { cId ->
                        containers[cId]?.let { cont ->
                            replaced[cont.id] = cont.snapshot()
                        }
                    }
                }
            }
        }
        applyOps(txn.operations())
        if (txn.addToBackStack) {
            backStack.add(BackStackEntry(txn.backStackName, txn.operations(), replaced, replacedStates))
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
            val vm = state.viewModel.toSortedMap().entries.joinToString(", ") { "${'$'}{it.key}=${'$'}{it.value}" }
            val ss = state.savedState.toSortedMap().entries.joinToString(", ") { "${'$'}{it.key}=${'$'}{it.value}" }
            val bd = state.binding.toSortedMap().entries.joinToString(", ") { "${'$'}{it.key}=${'$'}{it.value}" }
            val childs = state.children.sorted().joinToString(", ")
            builder.append("fragment=").append(name)
                .append(" parent=").append(parent)
                .append(" hidden=").append(state.hidden)
                .append(" detached=").append(state.detached)
                .append(" lifecycle=").append(state.lifecycle)
                .append(" maxLifecycle=").append(state.maxLifecycle)
                .append(" viewModel={").append(vm).append("}")
                .append(" savedState={").append(ss).append("}")
                .append(" binding={").append(bd).append("}")
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
                    fragState.detached = false
                    fragState.hidden = false
                    fragState.lifecycle = Lifecycle.RESUMED
                    fragState.lifecycle = minLifecycle(fragState.lifecycle, fragState.maxLifecycle)
                    fragState.lastContainer = op.container
                    container.add(op.fragment)
                }
                is TransactionOp.AddChild -> {
                    allContainersEverUsed.add(op.childContainer)
                    val parentState = fragmentStates[op.parentFragment]
                    if (parentState == null) continue
                    if (parentState.detached) continue
                    val childState = fragmentStates.getOrPut(op.childFragment.name) { FragmentState(op.childFragment) }
                    childState.parent = op.parentFragment
                    childState.hidden = false
                    childState.detached = false
                    childState.lifecycle = Lifecycle.RESUMED
                    parentState.children.add(op.childFragment.name)
                    childState.lastContainer = op.childContainer
                    val container = containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    container.add(op.childFragment)
                }
                is TransactionOp.Replace -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val oldList = container.snapshot()
                    for (old in oldList) {
                        container.remove(old)
                        fragmentStates[old.name]?.let { st ->
                            for (childName in st.children) {
                                fragmentStates.remove(childName)
                                for (c in containers.values) c.remove(Fragment(childName))
                            }
                        }
                        fragmentStates.remove(old.name)
                    }
                    container.replace(op.fragment)
                    val newState = fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                    newState.parent = null
                    newState.hidden = false
                    newState.detached = false
                    newState.lifecycle = Lifecycle.RESUMED
                    newState.lastContainer = op.container
                }
                is TransactionOp.Remove -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    for (c in containers.values) c.remove(op.fragment)
                    if (state.parent != null) {
                        fragmentStates[state.parent]?.children?.remove(op.fragment.name)
                    }
                    val toRemove = mutableListOf<String>()
                    toRemove.add(op.fragment.name)
                    var idx = 0
                    while (idx < toRemove.size) {
                        val cur = toRemove[idx]
                        val curState = fragmentStates[cur]
                        if (curState != null) {
                            toRemove.addAll(curState.children)
                        }
                        idx++
                    }
                    for (fn in toRemove) {
                        fragmentStates[fn]?.let { st ->
                            for (c in containers.values) c.remove(Fragment(fn))
                        }
                        fragmentStates.remove(fn)
                    }
                }
                is TransactionOp.Hide -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.hidden = true
                    state.lifecycle = minLifecycle(Lifecycle.STARTED, state.maxLifecycle)
                }
                is TransactionOp.Show -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.hidden = false
                    state.lifecycle = Lifecycle.RESUMED
                }
                is TransactionOp.Detach -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    for (c in containers.values) c.remove(op.fragment)
                    state.detached = true
                    state.lifecycle = Lifecycle.CREATED
                }
                is TransactionOp.Attach -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    if (!state.detached) continue
                    state.detached = false
                    state.lifecycle = minLifecycle(Lifecycle.RESUMED, state.maxLifecycle)
                    state.lastContainer?.let { lc ->
                        val container = containers.getOrPut(lc) { Container(lc) }
                        container.add(op.fragment)
                    }
                }
                is TransactionOp.SetMax -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.maxLifecycle = op.maxState
                    state.lifecycle = minLifecycle(state.lifecycle, state.maxLifecycle)
                    for (childName in state.children) {
                        fragmentStates[childName]?.let { child ->
                            child.maxLifecycle = minLifecycle(child.maxLifecycle, state.maxLifecycle)
                            child.lifecycle = minLifecycle(child.lifecycle, child.maxLifecycle)
                        }
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
                    fragmentStates.remove(op.fragment.name)
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
                        val snap = entry.replacedStates[frag.name]
                        if (snap != null) {
                            fragmentStates[frag.name] = snap.copy(
                                viewModel = snap.viewModel.toMutableMap(),
                                savedState = snap.savedState.toMutableMap(),
                                binding = snap.binding.toMutableMap(),
                                children = snap.children.toMutableSet()
                            )
                        } else {
                            fragmentStates.getOrPut(frag.name) { FragmentState(frag) }
                        }
                    }
                }
                is TransactionOp.Remove -> {
                    val snap = entry.replacedStates[op.fragment.name]
                    if (snap != null) {
                        fragmentStates[snap.fragment.name] = snap.copy(
                            viewModel = snap.viewModel.toMutableMap(),
                            savedState = snap.savedState.toMutableMap(),
                            binding = snap.binding.toMutableMap(),
                            children = snap.children.toMutableSet()
                        )
                        snap.lastContainer?.let { cId ->
                            val container = containers.getOrPut(cId) { Container(cId) }
                            container.add(Fragment(snap.fragment.name))
                            allContainersEverUsed.add(cId)
                        }
                    }
                }
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
                is TransactionOp.Detach -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.detached = false
                        it.lifecycle = Lifecycle.RESUMED
                        it.lastContainer?.let { lc ->
                            containers.getOrPut(lc) { Container(lc) }.add(op.fragment)
                        }
                    }
                }
                is TransactionOp.Attach -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.detached = true
                        it.lifecycle = Lifecycle.CREATED
                        for (c in containers.values) c.remove(op.fragment)
                    }
                }
                is TransactionOp.SetMax -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.maxLifecycle = Lifecycle.RESUMED
                        it.lifecycle = Lifecycle.RESUMED
                    }
                }
            }
        }
    }
}
