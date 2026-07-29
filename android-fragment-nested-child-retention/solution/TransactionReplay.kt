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
                    // Restore VM/SS if available
                    vmSave[op.fragment.name]?.let { vm -> state.viewModel.putAll(vm) }
                    ssSave[op.fragment.name]?.let { ss -> state.savedState.putAll(ss) }
                    allStates[op.fragment.name]?.let { cap ->
                        state.hidden = cap.hidden
                        state.viewModel.clear(); state.viewModel.putAll(cap.viewModel)
                        state.savedState.clear(); state.savedState.putAll(cap.savedState)
                        state.children.clear(); state.children.addAll(cap.children)
                        state.lifecycle = cap.lifecycle
                    }
                    if (state.hidden) state.lifecycle = Lifecycle.STARTED else state.lifecycle = Lifecycle.RESUMED
                }
                is TransactionOp.AddChild -> {
                    // Parent must exist in current recreated state
                    val parentState = fragmentStates[op.parentFragment] ?: continue
                    val container = containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    container.add(op.childFragment)
                    val childState = fragmentStates.getOrPut(op.childFragment.name) { FragmentState(op.childFragment) }
                    childState.parent = op.parentFragment
                    parentState.children.add(op.childFragment.name)
                    vmSave[op.childFragment.name]?.let { vm -> childState.viewModel.putAll(vm) }
                    ssSave[op.childFragment.name]?.let { ss -> childState.savedState.putAll(ss) }
                    allStates[op.childFragment.name]?.let { cap ->
                        childState.hidden = cap.hidden
                        childState.viewModel.clear(); childState.viewModel.putAll(cap.viewModel)
                        childState.savedState.clear(); childState.savedState.putAll(cap.savedState)
                        childState.children.clear(); childState.children.addAll(cap.children)
                        childState.lifecycle = cap.lifecycle
                    }
                    childState.lifecycle = when {
                        childState.hidden -> Lifecycle.STARTED
                        parentState.hidden -> Lifecycle.STARTED
                        else -> Lifecycle.RESUMED
                    }
                }
                is TransactionOp.Replace -> {
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    // Clear previous fragments in this container recursively
                    val prev = container.snapshot().toList()
                    for (pf in prev) {
                        // remove recursively
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
                    vmSave[op.fragment.name]?.let { vm -> state.viewModel.putAll(vm) }
                    ssSave[op.fragment.name]?.let { ss -> state.savedState.putAll(ss) }
                    state.hidden = false
                    state.lifecycle = Lifecycle.RESUMED
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
                        it.hidden = true
                        it.lifecycle = Lifecycle.STARTED
                    }
                }
                is TransactionOp.Show -> {
                    fragmentStates[op.fragment.name]?.let {
                        it.hidden = false
                        it.lifecycle = Lifecycle.RESUMED
                    }
                }
            }
        }
    }

    // Legacy overload for buggy path – kept for compilation compatibility
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
