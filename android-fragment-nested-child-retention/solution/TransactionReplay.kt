package com.example.fragment

object TransactionReplay {

    fun replayInto(
        containers: MutableMap<String, Container>,
        fragmentStates: MutableMap<String, FragmentState>,
        ops: List<TransactionOp>,
        allStates: Map<String, CapturedFragmentState> = emptyMap(),
        containerMap: Map<String, String> = emptyMap(),
        vmSave: Map<String, Map<String, String>> = emptyMap(),
        ssSave: Map<String, Map<String, String>> = emptyMap()
    ) {
        for (op in ops) {
            when (op) {
                is TransactionOp.Add -> {
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    container.add(op.fragment)
                    val state = fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                    state.parent = null
                    state.detached = false
                    vmSave[op.fragment.name]?.let { vm -> state.viewModel.putAll(vm) }
                    ssSave[op.fragment.name]?.let { ss -> state.savedState.putAll(ss) }
                    allStates[op.fragment.name]?.let { cap ->
                        state.hidden = cap.hidden
                        state.detached = cap.detached
                        state.viewModel.clear(); state.viewModel.putAll(cap.viewModel)
                        state.savedState.clear(); state.savedState.putAll(cap.savedState)
                        state.children.clear(); state.children.addAll(cap.children)
                        state.maxLifecycle = cap.maxLifecycle
                        state.lifecycle = cap.lifecycle
                        state.lastContainer = cap.lastContainer
                    }
                    state.lifecycle = minLifecycle(if (state.hidden) Lifecycle.STARTED else Lifecycle.RESUMED, state.maxLifecycle)
                    state.lastContainer = op.container
                }
                is TransactionOp.AddChild -> {
                    val parentState = fragmentStates[op.parentFragment] ?: continue
                    if (parentState.detached) continue
                    val container = containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    container.add(op.childFragment)
                    val childState = fragmentStates.getOrPut(op.childFragment.name) { FragmentState(op.childFragment) }
                    childState.parent = op.parentFragment
                    parentState.children.add(op.childFragment.name)
                    vmSave[op.childFragment.name]?.let { vm -> childState.viewModel.putAll(vm) }
                    ssSave[op.childFragment.name]?.let { ss -> childState.savedState.putAll(ss) }
                    allStates[op.childFragment.name]?.let { cap ->
                        childState.hidden = cap.hidden
                        childState.detached = cap.detached
                        childState.viewModel.clear(); childState.viewModel.putAll(cap.viewModel)
                        childState.savedState.clear(); childState.savedState.putAll(cap.savedState)
                        childState.children.clear(); childState.children.addAll(cap.children)
                        childState.maxLifecycle = cap.maxLifecycle
                        childState.lifecycle = cap.lifecycle
                        childState.lastContainer = cap.lastContainer
                    }
                    childState.lastContainer = op.childContainer
                    childState.maxLifecycle = minLifecycle(childState.maxLifecycle, parentState.maxLifecycle)
                    childState.lifecycle = when {
                        childState.detached -> Lifecycle.CREATED
                        childState.hidden -> minLifecycle(Lifecycle.STARTED, childState.maxLifecycle)
                        parentState.hidden -> minLifecycle(Lifecycle.STARTED, childState.maxLifecycle)
                        else -> minLifecycle(Lifecycle.RESUMED, childState.maxLifecycle)
                    }
                    childState.lifecycle = minLifecycle(childState.lifecycle, parentState.maxLifecycle)
                }
                is TransactionOp.Replace -> {
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    val prev = container.snapshot().toList()
                    for (pf in prev) {
                        fun removeRec(name: String) {
                            val st = fragmentStates[name] ?: return
                            for (ch in st.children.toList()) removeRec(ch)
                            for (c in containers.values) c.removeByName(name)
                            fragmentStates.remove(name)
                        }
                        removeRec(pf.name)
                    }
                    container.clear()
                    container.add(op.fragment)
                    val state = fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                    state.parent = null
                    state.detached = false
                    vmSave[op.fragment.name]?.let { vm -> state.viewModel.putAll(vm) }
                    ssSave[op.fragment.name]?.let { ss -> state.savedState.putAll(ss) }
                    state.lifecycle = minLifecycle(Lifecycle.RESUMED, state.maxLifecycle)
                    state.lastContainer = op.container
                }
                is TransactionOp.Remove -> {
                    fun removeRec(name: String) {
                        val st = fragmentStates[name] ?: return
                        for (ch in st.children.toList()) removeRec(ch)
                        for (c in containers.values) c.removeByName(name)
                        st.parent?.let { fragmentStates[it]?.children?.remove(name) }
                        fragmentStates.remove(name)
                    }
                    removeRec(op.fragment.name)
                }
                is TransactionOp.Hide -> {
                    fragmentStates[op.fragment.name]?.let {
                        if (it.detached) return@let
                        it.hidden = true
                        it.lifecycle = minLifecycle(Lifecycle.STARTED, it.maxLifecycle)
                    }
                }
                is TransactionOp.Show -> {
                    fragmentStates[op.fragment.name]?.let {
                        if (it.detached) return@let
                        it.hidden = false
                        it.lifecycle = minLifecycle(Lifecycle.RESUMED, it.maxLifecycle)
                    }
                }
                is TransactionOp.Detach -> {
                    val st = fragmentStates[op.fragment.name] ?: continue
                    st.lastContainer = containers.entries.find { e -> e.value.snapshot().any { ff -> ff.name == op.fragment.name } }?.key ?: st.lastContainer
                    for (c in containers.values) c.removeByName(op.fragment.name)
                    st.detached = true
                    st.lifecycle = Lifecycle.CREATED
                }
                is TransactionOp.Attach -> {
                    val st = fragmentStates[op.fragment.name] ?: continue
                    if (!st.detached) continue
                    st.detached = false
                    val lc = st.lastContainer
                    if (lc != null) {
                        containers.getOrPut(lc) { Container(lc) }.add(op.fragment)
                    }
                    st.lifecycle = minLifecycle(if (st.hidden) Lifecycle.STARTED else Lifecycle.RESUMED, st.maxLifecycle)
                }
                is TransactionOp.SetMax -> {
                    val st = fragmentStates[op.fragment.name] ?: continue
                    st.maxLifecycle = op.maxState
                    st.lifecycle = minLifecycle(st.lifecycle, st.maxLifecycle)
                }
            }
        }
    }

    fun replayInto(containers: MutableMap<String, Container>, ops: List<TransactionOp>) {
        for (op in ops) {
            when (op) {
                is TransactionOp.Add -> {
                    containers.getOrPut(op.container) { Container(op.container) }.add(op.fragment)
                }
                is TransactionOp.Replace -> {
                    containers.getOrPut(op.container) { Container(op.container) }.replace(op.fragment)
                }
                is TransactionOp.AddChild -> {
                    containers.getOrPut(op.childContainer) { Container(op.childContainer) }.add(op.childFragment)
                }
                is TransactionOp.Remove -> {
                    for (container in containers.values) container.remove(op.fragment)
                }
                else -> {}
            }
        }
    }
}
