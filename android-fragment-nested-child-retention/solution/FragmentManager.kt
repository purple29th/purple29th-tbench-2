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

    fun addToBackStack(txnId: String, name: String?) {
        openTransactions[txnId]?.markBackStack(name)
    }

    fun commit(txnId: String) {
        val txn = openTransactions.remove(txnId) ?: return

        val replaced = mutableMapOf<String, List<Fragment>>()
        val allCaptured = mutableMapOf<String, CapturedFragmentState>()
        val containerMap = mutableMapOf<String, String>()
        val hiddenSnap = mutableMapOf<String, Boolean>()
        val maxSnap = mutableMapOf<String, Lifecycle>()
        val detachedSnap = mutableMapOf<String, Boolean>()

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
                is TransactionOp.Hide, is TransactionOp.Show, is TransactionOp.Detach, is TransactionOp.Attach, is TransactionOp.SetMax -> {
                    val fragName = when (op) {
                        is TransactionOp.Hide -> op.fragment.name
                        is TransactionOp.Show -> op.fragment.name
                        is TransactionOp.Detach -> op.fragment.name
                        is TransactionOp.Attach -> op.fragment.name
                        is TransactionOp.SetMax -> op.fragment.name
                        else -> ""
                    }
                    fragmentStates[fragName]?.let {
                        hiddenSnap[fragName] = it.hidden
                        maxSnap[fragName] = it.maxLifecycle
                        detachedSnap[fragName] = it.detached
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
                    mapOf("global" to allCaptured.toMap()),
                    allCaptured.toMap(),
                    hiddenSnap.toMap(),
                    maxSnap.toMap(),
                    detachedSnap.toMap(),
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
        if (index < 0) return
        while (backStack.size > index) {
            reverseEntry(backStack.removeAt(backStack.size - 1))
        }
    }

    fun rotate() {
        val vmSave = fragmentStates.mapValues { it.value.viewModel.toMap() }
        val ssSave = fragmentStates.mapValues { it.value.savedState.toMap() }

        val saved = backStack.toList()

        for (c in containers.values) c.clear()
        fragmentStates.clear()

        backStack.clear()

        for (entry in saved) {
            TransactionReplay.replayInto(containers, fragmentStates, entry.ops, entry.allStates, entry.containerMap, vmSave, ssSave)
            backStack.add(entry)
        }

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
                .append(" detached=").append(state.detached)
                .append(" lifecycle=").append(state.lifecycle)
                .append(" maxLifecycle=").append(state.maxLifecycle)
                .append(" viewModel={").append(vm).append("}")
                .append(" savedState={").append(ss).append("}")
                .append(" children=[").append(childs).append("]\n")
        }
        val entries = backStack.joinToString(", ") { it.name ?: "anon" }
        builder.append("backstack=[").append(entries).append("]\n")
        return builder.toString()
    }

    private fun captureState(name: String): CapturedFragmentState? {
        val s = fragmentStates[name] ?: return null
        return CapturedFragmentState(
            parent = s.parent,
            hidden = s.hidden,
            detached = s.detached,
            lifecycle = s.lifecycle,
            maxLifecycle = s.maxLifecycle,
            lastContainer = s.lastContainer,
            viewModel = s.viewModel.toMap(),
            savedState = s.savedState.toMap(),
            children = s.children.toSet()
        )
    }

    private fun captureRecursive(name: String, out: MutableMap<String, CapturedFragmentState>, containerMap: MutableMap<String, String>) {
        if (out.containsKey(name)) return
        val cap = captureState(name) ?: return
        out[name] = cap
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
        for (child in state.children.toList()) {
            removeRecursive(child)
        }
        for (c in containers.values) c.removeByName(fragmentName)
        state.parent?.let { parentName ->
            fragmentStates[parentName]?.children?.remove(fragmentName)
        }
        fragmentStates.remove(fragmentName)
    }

    private fun downgradeChildrenToStarted(parentName: String) {
        val parentState = fragmentStates[parentName] ?: return
        for (childName in parentState.children) {
            val childState = fragmentStates[childName] ?: continue
            if (lifecycleOrder(childState.lifecycle) > lifecycleOrder(Lifecycle.STARTED)) {
                childState.lifecycle = minLifecycle(Lifecycle.STARTED, childState.maxLifecycle)
            }
            if (lifecycleOrder(childState.maxLifecycle) > lifecycleOrder(parentState.maxLifecycle)) {
                childState.maxLifecycle = parentState.maxLifecycle
                childState.lifecycle = minLifecycle(childState.lifecycle, childState.maxLifecycle)
            }
            downgradeChildrenToStarted(childName)
        }
    }

    private fun upgradeChildrenIfPossible(parentName: String) {
        val parentState = fragmentStates[parentName] ?: return
        if (parentState.hidden) return
        if (parentState.detached) return
        if (lifecycleOrder(parentState.lifecycle) < lifecycleOrder(Lifecycle.RESUMED)) return
        for (childName in parentState.children) {
            val childState = fragmentStates[childName] ?: continue
            if (childState.detached) continue
            if (childState.hidden) continue
            val desired = minLifecycle(Lifecycle.RESUMED, childState.maxLifecycle)
            if (lifecycleOrder(childState.lifecycle) < lifecycleOrder(desired)) {
                childState.lifecycle = minLifecycle(desired, parentState.maxLifecycle)
                childState.lifecycle = minLifecycle(childState.lifecycle, childState.maxLifecycle)
                upgradeChildrenIfPossible(childName)
            }
        }
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
                    fragState.detached = false
                    fragState.lifecycle = if (fragState.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                    fragState.lifecycle = minLifecycle(fragState.lifecycle, fragState.maxLifecycle)
                    fragState.lastContainer = op.container
                    container.add(op.fragment)
                }
                is TransactionOp.AddChild -> {
                    val parentState = fragmentStates[op.parentFragment]
                    if (parentState == null) continue
                    if (parentState.detached) continue
                    allContainersEverUsed.add(op.childContainer)
                    val childState = fragmentStates.getOrPut(op.childFragment.name) {
                        FragmentState(op.childFragment)
                    }
                    childState.parent?.let { oldParent ->
                        if (oldParent != op.parentFragment) {
                            fragmentStates[oldParent]?.children?.remove(op.childFragment.name)
                        }
                    }
                    childState.parent = op.parentFragment
                    childState.detached = false
                    childState.lastContainer = op.childContainer
                    childState.lifecycle = when {
                        childState.hidden -> Lifecycle.STARTED
                        childState.detached -> Lifecycle.CREATED
                        parentState.hidden -> Lifecycle.STARTED
                        else -> Lifecycle.RESUMED
                    }
                    childState.lifecycle = minLifecycle(childState.lifecycle, childState.maxLifecycle)
                    childState.lifecycle = minLifecycle(childState.lifecycle, parentState.maxLifecycle)
                    childState.maxLifecycle = minLifecycle(childState.maxLifecycle, parentState.maxLifecycle)
                    parentState.children.add(op.childFragment.name)
                    val container = containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    container.add(op.childFragment)
                }
                is TransactionOp.Replace -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val previous = container.snapshot()
                    for (prevFrag in previous) {
                        removeRecursive(prevFrag.name)
                    }
                    container.clear()
                    val newState = fragmentStates.getOrPut(op.fragment.name) {
                        FragmentState(op.fragment)
                    }
                    newState.parent = null
                    newState.detached = false
                    newState.lifecycle = if (newState.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                    newState.lifecycle = minLifecycle(newState.lifecycle, newState.maxLifecycle)
                    newState.lastContainer = op.container
                    container.add(op.fragment)
                }
                is TransactionOp.Remove -> {
                    removeRecursive(op.fragment.name)
                }
                is TransactionOp.Hide -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    if (state.detached) continue
                    state.hidden = true
                    state.lifecycle = minLifecycle(Lifecycle.STARTED, state.maxLifecycle)
                    downgradeChildrenToStarted(op.fragment.name)
                }
                is TransactionOp.Show -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    if (state.detached) continue
                    state.hidden = false
                    state.lifecycle = minLifecycle(Lifecycle.RESUMED, state.maxLifecycle)
                    if (state.parent != null && fragmentStates[state.parent]?.hidden == true) {
                        state.lifecycle = minLifecycle(Lifecycle.STARTED, state.maxLifecycle)
                    } else if (state.parent != null) {
                        val parentMax = fragmentStates[state.parent]?.maxLifecycle ?: Lifecycle.RESUMED
                        state.lifecycle = minLifecycle(state.lifecycle, parentMax)
                    }
                    upgradeChildrenIfPossible(op.fragment.name)
                }
                is TransactionOp.Detach -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.lastContainer = findContainerOf(op.fragment.name) ?: state.lastContainer
                    for (c in containers.values) c.removeByName(op.fragment.name)
                    state.detached = true
                    state.lifecycle = Lifecycle.CREATED
                    for (childName in state.children.toList()) {
                        val child = fragmentStates[childName] ?: continue
                        for (cc in containers.values) cc.removeByName(childName)
                        child.detached = true
                        child.lifecycle = Lifecycle.CREATED
                    }
                }
                is TransactionOp.Attach -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    if (!state.detached) continue
                    state.detached = false
                    val targetContainer = state.lastContainer
                    if (targetContainer != null) {
                        allContainersEverUsed.add(targetContainer)
                        val container = containers.getOrPut(targetContainer) { Container(targetContainer) }
                        container.add(op.fragment)
                    }
                    state.lifecycle = minLifecycle(if (state.hidden) Lifecycle.STARTED else Lifecycle.RESUMED, state.maxLifecycle)
                    for (childName in state.children) {
                        val child = fragmentStates[childName] ?: continue
                        if (!child.detached) continue
                        child.detached = false
                        val childContainer = child.lastContainer
                        if (childContainer != null) {
                            val cc = containers.getOrPut(childContainer) { Container(childContainer) }
                            cc.add(Fragment(childName))
                        }
                        child.lifecycle = minLifecycle(if (child.hidden) Lifecycle.STARTED else Lifecycle.RESUMED, child.maxLifecycle)
                        child.lifecycle = minLifecycle(child.lifecycle, state.maxLifecycle)
                    }
                }
                is TransactionOp.SetMax -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.maxLifecycle = op.maxState
                    state.lifecycle = minLifecycle(state.lifecycle, state.maxLifecycle)
                    for (childName in state.children) {
                        val child = fragmentStates[childName] ?: continue
                        if (lifecycleOrder(child.maxLifecycle) > lifecycleOrder(state.maxLifecycle)) {
                            child.maxLifecycle = state.maxLifecycle
                            child.lifecycle = minLifecycle(child.lifecycle, child.maxLifecycle)
                            // propagate further
                            val stack = mutableListOf(childName)
                            while (stack.isNotEmpty()) {
                                val cur = stack.removeAt(stack.size - 1)
                                val curSt = fragmentStates[cur] ?: continue
                                for (gc in curSt.children) {
                                    val gcSt = fragmentStates[gc] ?: continue
                                    if (lifecycleOrder(gcSt.maxLifecycle) > lifecycleOrder(curSt.maxLifecycle)) {
                                        gcSt.maxLifecycle = curSt.maxLifecycle
                                        gcSt.lifecycle = minLifecycle(gcSt.lifecycle, gcSt.maxLifecycle)
                                        stack.add(gc)
                                    }
                                }
                            }
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
                    removeRecursive(op.fragment.name)
                }
                is TransactionOp.AddChild -> {
                    removeRecursive(op.childFragment.name)
                }
                is TransactionOp.Replace -> {
                    val container = containers[op.container] ?: continue
                    removeRecursive(op.fragment.name)
                    container.clear()
                    val prevList = entry.replacedFragments[op.container] ?: emptyList()
                    for (frag in prevList) {
                        restoreRecursive(frag.name, entry)
                    }
                    for (frag in prevList) {
                        container.add(frag)
                    }
                }
                is TransactionOp.Remove -> {}
                is TransactionOp.Hide -> {
                    val st = fragmentStates[op.fragment.name] ?: continue
                    st.hidden = entry.hiddenSnapshot[op.fragment.name] ?: false
                    st.lifecycle = if (st.hidden) minLifecycle(Lifecycle.STARTED, st.maxLifecycle) else minLifecycle(Lifecycle.RESUMED, st.maxLifecycle)
                    if (!st.hidden) {
                        upgradeChildrenIfPossible(st.fragment.name)
                    } else {
                        downgradeChildrenToStarted(st.fragment.name)
                    }
                }
                is TransactionOp.Show -> {
                    val st = fragmentStates[op.fragment.name] ?: continue
                    st.hidden = entry.hiddenSnapshot[op.fragment.name] ?: true
                    st.lifecycle = if (st.hidden) minLifecycle(Lifecycle.STARTED, st.maxLifecycle) else minLifecycle(Lifecycle.RESUMED, st.maxLifecycle)
                    if (st.hidden) {
                        downgradeChildrenToStarted(st.fragment.name)
                    } else {
                        upgradeChildrenIfPossible(st.fragment.name)
                    }
                }
                is TransactionOp.Detach -> {
                    val st = fragmentStates[op.fragment.name] ?: continue
                    st.detached = entry.detachedSnapshot[op.fragment.name] ?: false
                    if (!st.detached) {
                        st.lifecycle = minLifecycle(if (st.hidden) Lifecycle.STARTED else Lifecycle.RESUMED, st.maxLifecycle)
                        val lc = st.lastContainer
                        if (lc != null) {
                            containers.getOrPut(lc) { Container(lc) }.add(op.fragment)
                        }
                    }
                }
                is TransactionOp.Attach -> {
                    val st = fragmentStates[op.fragment.name] ?: continue
                    st.detached = entry.detachedSnapshot[op.fragment.name] ?: true
                    st.lifecycle = if (st.detached) Lifecycle.CREATED else minLifecycle(Lifecycle.RESUMED, st.maxLifecycle)
                    if (st.detached) {
                        for (c in containers.values) c.remove(op.fragment)
                    }
                }
                is TransactionOp.SetMax -> {
                    val st = fragmentStates[op.fragment.name] ?: continue
                    st.maxLifecycle = entry.maxSnapshot[op.fragment.name] ?: Lifecycle.RESUMED
                    st.lifecycle = minLifecycle(st.lifecycle, st.maxLifecycle)
                }
            }
        }
    }

    private fun restoreRecursive(rootName: String, entry: BackStackEntry) {
        val captured = entry.allStates[rootName] ?: entry.replacedRootStates[rootName] ?: return
        val existing = fragmentStates[rootName]
        val state = if (existing != null) existing else FragmentState(Fragment(rootName)).also { fragmentStates[rootName] = it }
        state.parent = captured.parent
        state.hidden = captured.hidden
        state.detached = captured.detached
        state.lifecycle = captured.lifecycle
        state.maxLifecycle = captured.maxLifecycle
        state.lastContainer = captured.lastContainer
        state.viewModel.clear()
        state.viewModel.putAll(captured.viewModel)
        state.savedState.clear()
        state.savedState.putAll(captured.savedState)
        state.children.clear()
        state.children.addAll(captured.children)

        captured.parent?.let { parentName ->
            fragmentStates[parentName]?.children?.add(rootName)
        }

        val containerId = entry.containerMap[rootName]
        if (containerId != null) {
            allContainersEverUsed.add(containerId)
            val container = containers.getOrPut(containerId) { Container(containerId) }
            container.add(Fragment(rootName))
        }

        for (childName in captured.children) {
            restoreRecursive(childName, entry)
        }
    }
}
