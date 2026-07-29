package com.example.fragment

class FragmentManager {
    private val containers = mutableMapOf<String, Container>()
    private val fragmentStates = mutableMapOf<String, FragmentState>()
    private val openTransactions = mutableMapOf<String, Transaction>()
    private val backStack = mutableListOf<BackStackEntry>()
    private val allContainersEverUsed = mutableSetOf<String>()

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
        val allCaptured = mutableMapOf<String, CapturedFragmentState>()
        val containerMap = mutableMapOf<String, String>()
        val hiddenSnap = mutableMapOf<String, Boolean>()

        for (op in txn.operations()) {
            when (op) {
                is TransactionOp.Replace -> {
                    val container = containers[op.container]
                    if (container != null) {
                        val prev = container.snapshot()
                        if (prev.isNotEmpty()) {
                            replaced[op.container] = prev
                            for (frag in prev) {
                                captureRecursive(frag.name, allCaptured, containerMap)
                            }
                        }
                    }
                }
                is TransactionOp.Hide, is TransactionOp.Show -> {
                    val fragName = when (op) {
                        is TransactionOp.Hide -> op.fragment.name
                        is TransactionOp.Show -> op.fragment.name
                        else -> ""
                    }
                    fragmentStates[fragName]?.let { hiddenSnap[fragName] = it.hidden }
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
                    mapOf("global" to allCaptured.toMap()),
                    allCaptured.toMap(),
                    hiddenSnap.toMap(),
                    containerMap.toMap(),
                    allCaptured.toMap()
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
        val index = backStack.indexOfLast { it.name == name }
        if (index < 0) return // no-op
        while (backStack.size > index) {
            reverseEntry(backStack.removeAt(backStack.size - 1))
        }
    }

    fun rotate() {
        // Save viewModel and savedState for all current fragments before clearing
        val vmSave = fragmentStates.mapValues { it.value.viewModel.toMap() }
        val ssSave = fragmentStates.mapValues { it.value.savedState.toMap() }

        // Capture backstack
        val saved = backStack.toList()

        // Clear live containers and fragment states but NOT vmSave/ssSave maps
        for (c in containers.values) c.clear()
        fragmentStates.clear()

        backStack.clear()

        for (entry in saved) {
            // replay with retention
            TransactionReplay.replayInto(containers, fragmentStates, entry.ops, entry.allStates, entry.containerMap, vmSave, ssSave)
            backStack.add(entry)
        }

        // Restore viewModel/savedState for recreated fragments from saved maps if not already restored from allStates
        for ((fragName, vm) in vmSave) {
            if (fragmentStates.containsKey(fragName)) {
                val current = fragmentStates[fragName]!!
                for ((k, v) in vm) {
                    if (!current.viewModel.containsKey(k)) current.viewModel[k] = v
                }
            }
        }
        for ((fragName, ss) in ssSave) {
            if (fragmentStates.containsKey(fragName)) {
                val current = fragmentStates[fragName]!!
                for ((k, v) in ss) {
                    if (!current.savedState.containsKey(k)) current.savedState[k] = v
                }
            }
        }
    }

    fun snapshot(): String {
        val builder = StringBuilder()
        for ((id, container) in containers.toSortedMap()) {
            val frags = container.snapshot().map { it.name }.sorted()
            // Always print containers that have ever been used or currently have fragments
            if (frags.isEmpty() && !allContainersEverUsed.contains(id)) continue
            if (allContainersEverUsed.contains(id) || frags.isNotEmpty()) {
                builder.append("container=").append(id).append(" fragments=[").append(frags.joinToString(", ")).append("]\n")
            }
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

    // ---- helpers ----

    private fun captureState(name: String): CapturedFragmentState? {
        val s = fragmentStates[name] ?: return null
        return CapturedFragmentState(
            parent = s.parent,
            hidden = s.hidden,
            lifecycle = s.lifecycle,
            viewModel = s.viewModel.toMap(),
            savedState = s.savedState.toMap(),
            children = s.children.toSet()
        )
    }

    private fun captureRecursive(name: String, out: MutableMap<String, CapturedFragmentState>, containerMap: MutableMap<String, String>) {
        if (out.containsKey(name)) return
        val cap = captureState(name) ?: return
        out[name] = cap
        // Find container for this fragment
        findContainerOf(name)?.let { containerMap[name] = it }
        for (child in cap.children) {
            captureRecursive(child, out, containerMap)
        }
    }

    private fun findContainerOf(fragmentName: String): String? {
        for ((cid, cont) in containers) {
            if (cont.snapshot().any { it.name == fragmentName }) return cid
        }
        return null
    }

    private fun removeRecursive(fragmentName: String) {
        val state = fragmentStates[fragmentName] ?: return
        // First remove children recursively
        for (child in state.children.toList()) {
            removeRecursive(child)
        }
        // Remove from containers
        for (c in containers.values) {
            c.removeByName(fragmentName)
        }
        // Remove from parent's children set
        state.parent?.let { parentName ->
            fragmentStates[parentName]?.children?.remove(fragmentName)
        }
        fragmentStates.remove(fragmentName)
    }

    private fun applyOps(ops: List<TransactionOp>) {
        for (op in ops) {
            when (op) {
                is TransactionOp.Add -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val fragState = fragmentStates.getOrPut(op.fragment.name) {
                        FragmentState(op.fragment)
                    }
                    fragState.parent = null
                    fragState.lifecycle = if (fragState.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                    // Adjust lifecycle if parent hidden? root has no parent
                    container.add(op.fragment)
                }
                is TransactionOp.AddChild -> {
                    val parentState = fragmentStates[op.parentFragment]
                    if (parentState == null) continue // parent must exist
                    allContainersEverUsed.add(op.childContainer)
                    val childState = fragmentStates.getOrPut(op.childFragment.name) {
                        FragmentState(op.childFragment)
                    }
                    // If child already had a different parent, clean old parent link
                    childState.parent?.let { oldParent ->
                        if (oldParent != op.parentFragment) {
                            fragmentStates[oldParent]?.children?.remove(op.childFragment.name)
                        }
                    }
                    childState.parent = op.parentFragment
                    // lifecycle respects parent hidden and own hidden
                    childState.lifecycle = when {
                        childState.hidden -> Lifecycle.STARTED
                        parentState.hidden -> Lifecycle.STARTED
                        else -> Lifecycle.RESUMED
                    }
                    parentState.children.add(op.childFragment.name)
                    val container = containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    container.add(op.childFragment)
                }
                is TransactionOp.Replace -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val previous = container.snapshot()
                    // Remove previous fragments recursively
                    for (prevFrag in previous) {
                        removeRecursive(prevFrag.name)
                    }
                    container.clear()
                    val newState = fragmentStates.getOrPut(op.fragment.name) {
                        FragmentState(op.fragment)
                    }
                    newState.parent = null
                    newState.lifecycle = if (newState.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                    container.add(op.fragment)
                }
                is TransactionOp.Remove -> {
                    removeRecursive(op.fragment.name)
                }
                is TransactionOp.Hide -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.hidden = true
                    state.lifecycle = Lifecycle.STARTED
                    // Downgrade children
                    downgradeChildrenToStarted(op.fragment.name)
                }
                is TransactionOp.Show -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.hidden = false
                    state.lifecycle = Lifecycle.RESUMED
                    // If parent hidden, keep STARTED
                    if (state.parent != null && fragmentStates[state.parent]?.hidden == true) {
                        state.lifecycle = Lifecycle.STARTED
                    }
                    // Try to upgrade children if they are not hidden themselves
                    upgradeChildrenIfPossible(op.fragment.name)
                }
            }
        }
    }

    private fun downgradeChildrenToStarted(parentName: String) {
        val parentState = fragmentStates[parentName] ?: return
        for (childName in parentState.children) {
            val childState = fragmentStates[childName] ?: continue
            if (childState.lifecycle == Lifecycle.RESUMED) {
                childState.lifecycle = Lifecycle.STARTED
            }
            downgradeChildrenToStarted(childName)
        }
    }

    private fun upgradeChildrenIfPossible(parentName: String) {
        val parentState = fragmentStates[parentName] ?: return
        if (parentState.hidden) return
        if (parentState.lifecycle != Lifecycle.RESUMED) return
        for (childName in parentState.children) {
            val childState = fragmentStates[childName] ?: continue
            if (!childState.hidden && childState.lifecycle == Lifecycle.STARTED) {
                childState.lifecycle = Lifecycle.RESUMED
                upgradeChildrenIfPossible(childName)
            }
        }
    }

    private fun reverseEntry(entry: BackStackEntry) {
        for (op in entry.ops.reversed()) {
            when (op) {
                is TransactionOp.Add -> {
                    removeRecursive(op.fragment.name)
                }
                is TransactionOp.AddChild -> {
                    removeRecursive(op.childFragment.name)
                }
                is TransactionOp.Replace -> {
                    val container = containers[op.container] ?: continue
                    // Remove new fragment recursively
                    removeRecursive(op.fragment.name)
                    container.clear()
                    val prevList = entry.replacedFragments[op.container] ?: emptyList()
                    // Restore each previous fragment with its full subtree
                    for (frag in prevList) {
                        restoreRecursive(frag.name, entry)
                    }
                    // Re-add root fragments to this container in original order
                    for (frag in prevList) {
                        container.add(frag)
                    }
                }
                is TransactionOp.Remove -> {
                    // For simplicity we do not restore removed fragments on pop reverse unless they were captured
                    // Original task's Remove reverse is no-op, but for nested we keep no-op
                }
                is TransactionOp.Hide -> {
                    val st = fragmentStates[op.fragment.name] ?: continue
                    st.hidden = entry.hiddenSnapshot[op.fragment.name] ?: false
                    st.lifecycle = if (st.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                    if (!st.hidden) {
                        upgradeChildrenIfPossible(st.fragment.name)
                    }
                }
                is TransactionOp.Show -> {
                    val st = fragmentStates[op.fragment.name] ?: continue
                    st.hidden = entry.hiddenSnapshot[op.fragment.name] ?: true
                    st.lifecycle = if (st.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                    if (st.hidden) {
                        downgradeChildrenToStarted(st.fragment.name)
                    }
                }
            }
        }
    }

    private fun restoreRecursive(rootName: String, entry: BackStackEntry) {
        val captured = entry.allStates[rootName] ?: entry.replacedRootStates[rootName] ?: return
        // Create or overwrite state
        val existing = fragmentStates[rootName]
        val state = if (existing != null) existing else FragmentState(Fragment(rootName)).also { fragmentStates[rootName] = it }
        state.parent = captured.parent
        state.hidden = captured.hidden
        state.lifecycle = captured.lifecycle
        state.viewModel.clear()
        state.viewModel.putAll(captured.viewModel)
        state.savedState.clear()
        state.savedState.putAll(captured.savedState)
        state.children.clear()
        state.children.addAll(captured.children)

        // Restore parent link
        captured.parent?.let { parentName ->
            fragmentStates[parentName]?.children?.add(rootName)
        }

        // Restore container membership
        val containerId = entry.containerMap[rootName]
        if (containerId != null) {
            allContainersEverUsed.add(containerId)
            val container = containers.getOrPut(containerId) { Container(containerId) }
            container.add(Fragment(rootName))
        }

        // Recursively restore children
        for (childName in captured.children) {
            restoreRecursive(childName, entry)
        }
    }
}
