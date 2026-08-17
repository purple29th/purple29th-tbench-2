package com.example.fragment

object TransactionReplay {
    fun replayInto(
        containers: MutableMap<String, Container>,
        fragmentStates: MutableMap<String, FragmentState>,
        ops: List<TransactionOp>,
        allContainersEverUsed: MutableSet<String>
    ) {
        for (op in ops) {
            when (op) {
                is TransactionOp.Add -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val fragState = fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                    fragState.parent = null
                    fragState.detached = false
                    fragState.hidden = false
                    fragState.lifecycle = minLifecycle(Lifecycle.RESUMED, fragState.maxLifecycle)
                    fragState.lastContainer = op.container
                    fragState.binding.clear()
                    container.add(op.fragment)
                }
                is TransactionOp.AddChild -> {
                    allContainersEverUsed.add(op.childContainer)
                    containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    val parentState = fragmentStates[op.parentFragment] ?: continue
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
                        if (curState != null) toRemove.addAll(curState.children.filter { it !in toRemove })
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
}
