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
                    fragState.lifecycle = Lifecycle.RESUMED
                    fragState.binding.clear()
                    container.add(op.fragment)
                }
                is TransactionOp.AddChild -> {
                    allContainersEverUsed.add(op.childContainer)
                    val parentState = fragmentStates[op.parentFragment]
                    val childState = fragmentStates.getOrPut(op.childFragment.name) { FragmentState(op.childFragment) }
                    childState.parent = op.parentFragment
                    childState.lifecycle = Lifecycle.RESUMED
                    childState.binding.clear()
                    parentState?.children?.add(op.childFragment.name)
                    val container = containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    container.add(op.childFragment)
                }
                is TransactionOp.Replace -> {
                    allContainersEverUsed.add(op.container)
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    container.replace(op.fragment)
                    val newState = fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                    newState.parent = null
                    newState.binding.clear()
                }
                else -> {}
            }
        }
    }
}
