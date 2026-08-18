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
                    // capture all descendants of replaced fragments
                    val queue = replaced[op.container]!!.map { it.name }.toMutableList()
                    var i = 0
                    while (i < queue.size) {
                        val curName = queue[i]
                        val curState = fragmentStates[curName]
                        if (curState != null) {
                            for (child in curState.children) {
                                if (child !in queue) queue.add(child)
                                fragmentStates[child]?.let { childSt ->
                                    replacedStates[child] = childSt.copy(
                                        viewModel = childSt.viewModel.toMutableMap(),
                                        savedState = childSt.savedState.toMutableMap(),
                                        binding = childSt.binding.toMutableMap(),
                                        children = childSt.children.toMutableSet()
                                    )
                                }
                            }
                        }
                        i++
                    }
                }
            }
            if (op is TransactionOp.Remove) {
                val st = fragmentStates[op.fragment.name]
                if (st != null) {
                    // capture to allow restore on pop
                    replacedStates[op.fragment.name] = st.copy(
                        viewModel = st.viewModel.toMutableMap(),
                        savedState = st.savedState.toMutableMap(),
                        binding = st.binding.toMutableMap(),
                        children = st.children.toMutableSet()
                    )
                    st.lastContainer?.let { cId ->
                        containers[cId]?.let { cont ->
                            replaced[cId] = cont.snapshot()
                        }
                    }
                    // capture descendants
                    val queue = mutableListOf(op.fragment.name)
                    queue.addAll(st.children)
                    var idx = 0
                    while (idx < queue.size) {
                        val curName = queue[idx]
                        val curState = fragmentStates[curName]
                        if (curState != null && curName != op.fragment.name) {
                            replacedStates[curName] = curState.copy(
                                viewModel = curState.viewModel.toMutableMap(),
                                savedState = curState.savedState.toMutableMap(),
                                binding = curState.binding.toMutableMap(),
                                children = curState.children.toMutableSet()
                            )
                            for (child in curState.children) if (child !in queue) queue.add(child)
                        } else if (curState != null) {
                            for (child in curState.children) if (child !in queue) queue.add(child)
                        }
                        idx++
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
            val entry = backStack.removeAt(backStack.size - 1)
            reverseEntry(entry)
            return
        }
        val index = backStack.indexOfLast { it.name == name }
        if (index < 0) return // no-op, do NOT drain
        while (backStack.size > index) {
            val entry = backStack.removeAt(backStack.size - 1)
            reverseEntry(entry)
        }
    }

    fun rotate() {
        // save viewModel and savedState before clearing, as they survive rotate unlike binding
        val vmSave = fragmentStates.mapValues { it.value.viewModel.toMap() }
        val ssSave = fragmentStates.mapValues { it.value.savedState.toMap() }

        for (container in containers.values) container.clear()
        fragmentStates.clear()
        val saved = backStack.toList()
        backStack.clear()
        for (entry in saved) {
            applyOpsForRotate(entry.ops)
            backStack.add(entry)
        }
        // restore viewModel and savedState for fragments that survived replay, binding stays empty
        for ((fragName, vm) in vmSave) {
            if (fragmentStates.containsKey(fragName)) {
                val cur = fragmentStates[fragName]!!
                for ((k, v) in vm) {
                    if (!cur.viewModel.containsKey(k)) cur.viewModel[k] = v
                }
            }
        }
        for ((fragName, ss) in ssSave) {
            if (fragmentStates.containsKey(fragName)) {
                val cur = fragmentStates[fragName]!!
                for ((k, v) in ss) {
                    if (!cur.savedState.containsKey(k)) cur.savedState[k] = v
                }
            }
        }
        // ensure all bindings are empty after rotate
        for (fs in fragmentStates.values) fs.binding.clear()
    }

    private fun applyOpsForRotate(ops: List<TransactionOp>) {
        for (op in ops) {
            when (op) {
                is TransactionOp.Add -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val fs = fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                    fs.parent = null
                    fs.detached = false
                    fs.hidden = false
                    fs.lifecycle = minLifecycle(Lifecycle.RESUMED, fs.maxLifecycle)
                    fs.lastContainer = op.container
                    fs.binding.clear()
                    container.add(op.fragment)
                }
                is TransactionOp.AddChild -> {
                    allContainersEverUsed.add(op.childContainer)
                    containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    val parentState = fragmentStates[op.parentFragment]
                    if (parentState == null) continue
                    if (parentState.detached) continue
                    val childState = fragmentStates.getOrPut(op.childFragment.name) { FragmentState(op.childFragment) }
                    childState.parent = op.parentFragment
                    childState.detached = false
                    childState.hidden = false
                    var target = Lifecycle.RESUMED
                    target = minLifecycle(target, childState.maxLifecycle)
                    target = minLifecycle(target, parentState.maxLifecycle)
                    if (parentState.hidden) target = minLifecycle(Lifecycle.STARTED, target)
                    childState.lifecycle = target
                    parentState.children.add(op.childFragment.name)
                    childState.lastContainer = op.childContainer
                    childState.binding.clear()
                    val container = containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    container.add(op.childFragment)
                }
                is TransactionOp.Replace -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val oldList = container.snapshot().toList()
                    for (old in oldList) {
                        val oldState = fragmentStates[old.name]
                        if (oldState != null) {
                            val queue = mutableListOf<String>()
                            queue.add(old.name)
                            queue.addAll(oldState.children)
                            var idx = 0
                            while (idx < queue.size) {
                                val curName = queue[idx]
                                val curSt = fragmentStates[curName]
                                if (curSt != null) {
                                    for (child in curSt.children) if (child !in queue) queue.add(child)
                                }
                                idx++
                            }
                            for (fn in queue) {
                                fragmentStates[fn]?.let {
                                    for (c in containers.values) c.remove(Fragment(fn))
                                    if (it.parent != null) fragmentStates[it.parent]?.children?.remove(fn)
                                }
                                fragmentStates.remove(fn)
                            }
                        } else {
                            container.remove(old)
                        }
                    }
                    container.replace(op.fragment)
                    val newState = fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                    newState.parent = null
                    newState.hidden = false
                    newState.detached = false
                    newState.lifecycle = minLifecycle(Lifecycle.RESUMED, newState.maxLifecycle)
                    newState.lastContainer = op.container
                    newState.binding.clear()
                }
                is TransactionOp.Remove -> {
                    if (!fragmentStates.containsKey(op.fragment.name)) continue
                    val toRemove = mutableListOf(op.fragment.name)
                    var idx = 0
                    while (idx < toRemove.size) {
                        val cur = toRemove[idx]
                        val curState = fragmentStates[cur]
                        if (curState != null) {
                            toRemove.addAll(curState.children.filter { it !in toRemove })
                        }
                        idx++
                    }
                    for (fn in toRemove) {
                        for (c in containers.values) c.remove(Fragment(fn))
                        fragmentStates[fn]?.let { st ->
                            if (st.parent != null) fragmentStates[st.parent]?.children?.remove(fn)
                        }
                        fragmentStates.remove(fn)
                    }
                }
                is TransactionOp.Hide -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.hidden = true
                    state.lifecycle = minLifecycle(Lifecycle.STARTED, state.maxLifecycle)
                    state.binding.clear()
                    // propagate binding clear only, NOT lifecycle downgrade for children
                    val queue = state.children.toMutableList()
                    var idx = 0
                    while (idx < queue.size) {
                        val curName = queue[idx]
                        val curSt = fragmentStates[curName]
                        if (curSt != null) {
                            curSt.binding.clear()
                            queue.addAll(curSt.children)
                        }
                        idx++
                    }
                }
                is TransactionOp.Show -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.hidden = false
                    val parentMax = state.parent?.let { fragmentStates[it]?.maxLifecycle } ?: Lifecycle.RESUMED
                    val parentHidden = state.parent?.let { fragmentStates[it]?.hidden } ?: false
                    val parentDetached = state.parent?.let { fragmentStates[it]?.detached } ?: false
                    var target = Lifecycle.RESUMED
                    if (parentHidden || parentDetached) target = Lifecycle.STARTED
                    target = minLifecycle(target, state.maxLifecycle)
                    target = minLifecycle(target, parentMax)
                    state.lifecycle = target
                    state.binding.clear()
                    val queue = state.children.toMutableList()
                    var cIdx = 0
                    while (cIdx < queue.size) {
                        val curName = queue[cIdx]
                        val curSt = fragmentStates[curName]
                        if (curSt != null) {
                            if (!curSt.hidden && !curSt.detached) {
                                val pMax = curSt.parent?.let { fragmentStates[it]?.maxLifecycle } ?: Lifecycle.RESUMED
                                val pHidden = curSt.parent?.let { fragmentStates[it]?.hidden } ?: false
                                val pDetached = curSt.parent?.let { fragmentStates[it]?.detached } ?: false
                                var t = Lifecycle.RESUMED
                                if (pHidden || pDetached) t = Lifecycle.STARTED
                                t = minLifecycle(t, curSt.maxLifecycle)
                                t = minLifecycle(t, pMax)
                                curSt.lifecycle = t
                                curSt.binding.clear()
                            }
                            queue.addAll(curSt.children)
                        }
                        cIdx++
                    }
                }
                is TransactionOp.Detach -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    val queue = mutableListOf<String>()
                    queue.add(op.fragment.name)
                    queue.addAll(state.children)
                    var idx = 0
                    while (idx < queue.size) {
                        val curName = queue[idx]
                        val curSt = fragmentStates[curName]
                        if (curSt != null) {
                            for (c in containers.values) c.remove(Fragment(curName))
                            curSt.detached = true
                            curSt.lifecycle = Lifecycle.CREATED
                            curSt.binding.clear()
                            queue.addAll(curSt.children)
                        }
                        idx++
                    }
                }
                is TransactionOp.Attach -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    if (!state.detached) continue
                    state.detached = false
                    val parentMax = state.parent?.let { fragmentStates[it]?.maxLifecycle } ?: Lifecycle.RESUMED
                    val parentHidden = state.parent?.let { fragmentStates[it]?.hidden } ?: false
                    val parentDetached = state.parent?.let { fragmentStates[it]?.detached } ?: false
                    var target = if (state.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                    if (parentHidden || parentDetached) target = Lifecycle.STARTED
                    target = minLifecycle(target, state.maxLifecycle)
                    target = minLifecycle(target, parentMax)
                    state.lifecycle = target
                    state.binding.clear()
                    state.lastContainer?.let { lc ->
                        val container = containers.getOrPut(lc) { Container(lc) }
                        container.add(op.fragment)
                    }
                    val queue = state.children.toMutableList()
                    var idx = 0
                    while (idx < queue.size) {
                        val curName = queue[idx]
                        val curSt = fragmentStates[curName]
                        if (curSt != null) {
                            curSt.detached = false
                            val pMax = curSt.parent?.let { fragmentStates[it]?.maxLifecycle } ?: Lifecycle.RESUMED
                            val pHidden = curSt.parent?.let { fragmentStates[it]?.hidden } ?: false
                            val pDetached = curSt.parent?.let { fragmentStates[it]?.detached } ?: false
                            var t = if (curSt.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                            if (pHidden || pDetached) t = Lifecycle.STARTED
                            t = minLifecycle(t, curSt.maxLifecycle)
                            t = minLifecycle(t, pMax)
                            curSt.lifecycle = t
                            curSt.binding.clear()
                            curSt.lastContainer?.let { lc2 ->
                                val container = containers.getOrPut(lc2) { Container(lc2) }
                                container.add(Fragment(curName))
                            }
                            queue.addAll(curSt.children)
                        }
                        idx++
                    }
                }
                is TransactionOp.SetMax -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.maxLifecycle = op.maxState
                    state.lifecycle = minLifecycle(state.lifecycle, state.maxLifecycle)
                    val queue = state.children.toMutableList()
                    var idx = 0
                    while (idx < queue.size) {
                        val curName = queue[idx]
                        val curSt = fragmentStates[curName]
                        if (curSt != null) {
                            curSt.maxLifecycle = minLifecycle(curSt.maxLifecycle, state.maxLifecycle)
                            curSt.lifecycle = minLifecycle(curSt.lifecycle, curSt.maxLifecycle)
                            queue.addAll(curSt.children)
                        }
                        idx++
                    }
                }
            }
        }
    }

    fun snapshot(): String {
        val builder = StringBuilder()
        for (id in allContainersEverUsed.toSortedSet()) {
            val container = containers[id]
            val frags = container?.snapshot()?.map { it.name }?.sorted() ?: emptyList()
            builder.append("container=").append(id).append(" fragments=[").append(frags.joinToString(", ")).append("]\n")
        }
        for ((name, state) in fragmentStates.toSortedMap()) {
            val parent = state.parent ?: "NONE"
            val vm = state.viewModel.toSortedMap().entries.joinToString(", ") { "${it.key}=${it.value}" }
            val ss = state.savedState.toSortedMap().entries.joinToString(", ") { "${it.key}=${it.value}" }
            val bd = state.binding.toSortedMap().entries.joinToString(", ") { "${it.key}=${it.value}" }
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
                    fragState.binding.clear()
                    container.add(op.fragment)
                }
                is TransactionOp.AddChild -> {
                    allContainersEverUsed.add(op.childContainer)
                    val parentState = fragmentStates[op.parentFragment] ?: continue
                    if (parentState.detached) continue
                    val childState = fragmentStates.getOrPut(op.childFragment.name) { FragmentState(op.childFragment) }
                    childState.parent = op.parentFragment
                    childState.detached = false
                    childState.hidden = false
                    childState.lifecycle = Lifecycle.RESUMED
                    childState.lifecycle = minLifecycle(childState.lifecycle, childState.maxLifecycle)
                    childState.lifecycle = minLifecycle(childState.lifecycle, parentState.maxLifecycle)
                    if (parentState.hidden) {
                        childState.lifecycle = minLifecycle(Lifecycle.STARTED, childState.lifecycle)
                    }
                    parentState.children.add(op.childFragment.name)
                    childState.lastContainer = op.childContainer
                    childState.binding.clear()
                    val container = containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    container.add(op.childFragment)
                }
                is TransactionOp.Replace -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val oldList = container.snapshot().toList()
                    for (old in oldList) {
                        val oldState = fragmentStates[old.name]
                        if (oldState != null) {
                            // recursively remove children
                            val queue = mutableListOf(old.name)
                            queue.addAll(oldState.children)
                            var idx = 0
                            while (idx < queue.size) {
                                val curName = queue[idx]
                                val curSt = fragmentStates[curName]
                                if (curSt != null) {
                                    for (child in curSt.children) if (child !in queue) queue.add(child)
                                }
                                idx++
                            }
                            for (fn in queue) {
                                fragmentStates[fn]?.let {
                                    for (c in containers.values) c.remove(Fragment(fn))
                                    if (it.parent != null) fragmentStates[it.parent]?.children?.remove(fn)
                                }
                                fragmentStates.remove(fn)
                            }
                        } else {
                            container.remove(old)
                        }
                    }
                    container.replace(op.fragment)
                    val newState = fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                    newState.parent = null
                    newState.hidden = false
                    newState.detached = false
                    newState.lifecycle = Lifecycle.RESUMED
                    newState.lifecycle = minLifecycle(newState.lifecycle, newState.maxLifecycle)
                    newState.lastContainer = op.container
                    newState.binding.clear()
                }
                is TransactionOp.Remove -> {
                    if (!fragmentStates.containsKey(op.fragment.name)) continue
                    val toRemove = mutableListOf(op.fragment.name)
                    var idx = 0
                    while (idx < toRemove.size) {
                        val cur = toRemove[idx]
                        val curState = fragmentStates[cur]
                        if (curState != null) {
                            toRemove.addAll(curState.children.filter { it !in toRemove })
                        }
                        idx++
                    }
                    for (fn in toRemove) {
                        for (c in containers.values) c.remove(Fragment(fn))
                        fragmentStates[fn]?.let { st ->
                            if (st.parent != null) fragmentStates[st.parent]?.children?.remove(fn)
                        }
                        fragmentStates.remove(fn)
                    }
                }
                is TransactionOp.Hide -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.hidden = true
                    state.lifecycle = minLifecycle(Lifecycle.STARTED, state.maxLifecycle)
                    state.binding.clear()
                    // propagate binding clear only, NOT lifecycle downgrade for children
                    val queue = state.children.toMutableList()
                    var idx = 0
                    while (idx < queue.size) {
                        val curName = queue[idx]
                        val curSt = fragmentStates[curName]
                        if (curSt != null) {
                            curSt.binding.clear()
                            queue.addAll(curSt.children)
                        }
                        idx++
                    }
                }
                is TransactionOp.Show -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.hidden = false
                    val parentMax = state.parent?.let { fragmentStates[it]?.maxLifecycle } ?: Lifecycle.RESUMED
                    val parentHidden = state.parent?.let { fragmentStates[it]?.hidden } ?: false
                    val parentDetached = state.parent?.let { fragmentStates[it]?.detached } ?: false
                    var target = Lifecycle.RESUMED
                    if (parentHidden || parentDetached) target = Lifecycle.STARTED
                    target = minLifecycle(target, state.maxLifecycle)
                    target = minLifecycle(target, parentMax)
                    state.lifecycle = target
                    state.binding.clear()
                    // propagate to children
                    val queue = state.children.toMutableList()
                    var idx = 0
                    while (idx < queue.size) {
                        val curName = queue[idx]
                        val curSt = fragmentStates[curName]
                        if (curSt != null) {
                            if (!curSt.hidden && !curSt.detached) {
                                val pMax = curSt.parent?.let { fragmentStates[it]?.maxLifecycle } ?: Lifecycle.RESUMED
                                val pHidden = curSt.parent?.let { fragmentStates[it]?.hidden } ?: false
                                val pDetached = curSt.parent?.let { fragmentStates[it]?.detached } ?: false
                                var t = Lifecycle.RESUMED
                                if (pHidden || pDetached) t = Lifecycle.STARTED
                                t = minLifecycle(t, curSt.maxLifecycle)
                                t = minLifecycle(t, pMax)
                                curSt.lifecycle = t
                                curSt.binding.clear()
                            }
                            queue.addAll(curSt.children)
                        }
                        idx++
                    }
                }
                is TransactionOp.Detach -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    // remove from containers and clear binding for self and children
                    val queue = mutableListOf(op.fragment.name)
                    queue.addAll(state.children)
                    var idx = 0
                    while (idx < queue.size) {
                        val curName = queue[idx]
                        val curSt = fragmentStates[curName]
                        if (curSt != null) {
                            for (c in containers.values) c.remove(Fragment(curName))
                            curSt.detached = true
                            curSt.lifecycle = Lifecycle.CREATED
                            curSt.binding.clear()
                            queue.addAll(curSt.children)
                        }
                        idx++
                    }
                }
                is TransactionOp.Attach -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    if (!state.detached) continue
                    state.detached = false
                    val parentMax = state.parent?.let { fragmentStates[it]?.maxLifecycle } ?: Lifecycle.RESUMED
                    val parentHidden = state.parent?.let { fragmentStates[it]?.hidden } ?: false
                    val parentDetached = state.parent?.let { fragmentStates[it]?.detached } ?: false
                    var target = if (state.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                    if (parentHidden || parentDetached) target = Lifecycle.STARTED
                    target = minLifecycle(target, state.maxLifecycle)
                    target = minLifecycle(target, parentMax)
                    state.lifecycle = target
                    state.binding.clear()
                    state.lastContainer?.let { lc ->
                        val container = containers.getOrPut(lc) { Container(lc) }
                        container.add(op.fragment)
                    }
                    // restore children
                    val queue = state.children.toMutableList()
                    var idx = 0
                    while (idx < queue.size) {
                        val curName = queue[idx]
                        val curSt = fragmentStates[curName]
                        if (curSt != null) {
                            curSt.detached = false
                            val pMax = curSt.parent?.let { fragmentStates[it]?.maxLifecycle } ?: Lifecycle.RESUMED
                            val pHidden = curSt.parent?.let { fragmentStates[it]?.hidden } ?: false
                            val pDetached = curSt.parent?.let { fragmentStates[it]?.detached } ?: false
                            var t = if (curSt.hidden) Lifecycle.STARTED else Lifecycle.RESUMED
                            if (pHidden || pDetached) t = Lifecycle.STARTED
                            t = minLifecycle(t, curSt.maxLifecycle)
                            t = minLifecycle(t, pMax)
                            curSt.lifecycle = t
                            curSt.binding.clear()
                            curSt.lastContainer?.let { lc2 ->
                                val container = containers.getOrPut(lc2) { Container(lc2) }
                                container.add(Fragment(curName))
                            }
                            queue.addAll(curSt.children)
                        }
                        idx++
                    }
                }
                is TransactionOp.SetMax -> {
                    val state = fragmentStates[op.fragment.name] ?: continue
                    state.maxLifecycle = op.maxState
                    state.lifecycle = minLifecycle(state.lifecycle, state.maxLifecycle)
                    // cascade to descendants
                    val queue = state.children.toMutableList()
                    var idx = 0
                    while (idx < queue.size) {
                        val curName = queue[idx]
                        val curSt = fragmentStates[curName]
                        if (curSt != null) {
                            curSt.maxLifecycle = minLifecycle(curSt.maxLifecycle, state.maxLifecycle)
                            curSt.lifecycle = minLifecycle(curSt.lifecycle, curSt.maxLifecycle)
                            queue.addAll(curSt.children)
                        }
                        idx++
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
                                binding = mutableMapOf(), // binding always empty on restore
                                children = snap.children.toMutableSet()
                            )
                        } else {
                            fragmentStates.getOrPut(frag.name) { FragmentState(frag) }
                        }
                        allContainersEverUsed.add(op.container)
                    }
                }
                is TransactionOp.Remove -> {
                    val snap = entry.replacedStates[op.fragment.name]
                    if (snap != null) {
                        fragmentStates[snap.fragment.name] = snap.copy(
                            viewModel = snap.viewModel.toMutableMap(),
                            savedState = snap.savedState.toMutableMap(),
                            binding = mutableMapOf(),
                            children = snap.children.toMutableSet()
                        )
                        snap.lastContainer?.let { cId ->
                            val container = containers.getOrPut(cId) { Container(cId) }
                            container.add(Fragment(snap.fragment.name))
                            allContainersEverUsed.add(cId)
                        }
                        // restore descendants from captured states
                        val queue = snap.children.toMutableList()
                        var idx = 0
                        while (idx < queue.size) {
                            val curName = queue[idx]
                            val curSnap = entry.replacedStates[curName]
                            if (curSnap != null) {
                                fragmentStates[curName] = curSnap.copy(
                                    viewModel = curSnap.viewModel.toMutableMap(),
                                    savedState = curSnap.savedState.toMutableMap(),
                                    binding = mutableMapOf(),
                                    children = curSnap.children.toMutableSet()
                                )
                                curSnap.lastContainer?.let { cId ->
                                    containers.getOrPut(cId) { Container(cId) }.add(Fragment(curName))
                                    allContainersEverUsed.add(cId)
                                }
                                queue.addAll(curSnap.children)
                            }
                            idx++
                        }
                    }
                }
                is TransactionOp.Hide -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.hidden = false
                        it.lifecycle = minLifecycle(Lifecycle.RESUMED, it.maxLifecycle)
                        it.binding.clear()
                    }
                }
                is TransactionOp.Show -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.hidden = true
                        it.lifecycle = minLifecycle(Lifecycle.STARTED, it.maxLifecycle)
                        it.binding.clear()
                    }
                }
                is TransactionOp.Detach -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.detached = false
                        it.lifecycle = minLifecycle(Lifecycle.RESUMED, it.maxLifecycle)
                        it.binding.clear()
                        it.lastContainer?.let { lc ->
                            containers.getOrPut(lc) { Container(lc) }.add(op.fragment)
                        }
                    }
                }
                is TransactionOp.Attach -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.detached = true
                        it.lifecycle = Lifecycle.CREATED
                        it.binding.clear()
                        for (c in containers.values) c.remove(op.fragment)
                    }
                }
                is TransactionOp.SetMax -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.maxLifecycle = Lifecycle.RESUMED
                        it.lifecycle = minLifecycle(Lifecycle.RESUMED, it.maxLifecycle)
                    }
                }
            }
        }
    }
}
