package com.example.fragment

object TransactionReplay {
    fun replayInto(
        containers: MutableMap<String, Container>,
        fragmentStates: MutableMap<String, FragmentState>,
        ops: List<TransactionOp>
    ) {
        for (op in ops) {
            when (op) {
                is TransactionOp.Add -> {
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    container.add(op.fragment)
                    fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                }
                is TransactionOp.AddChild -> {
                    val container = containers.getOrPut(op.childContainer) { Container(op.childContainer) }
                    container.add(op.childFragment)
                    val childState = fragmentStates.getOrPut(op.childFragment.name) { FragmentState(op.childFragment) }
                    childState.parent = op.parentFragment
                    fragmentStates[op.parentFragment]?.children?.add(op.childFragment.name)
                }
                is TransactionOp.Replace -> {
                    val container = containers.getOrPut(op.container) { Container(op.container) }
                    container.replace(op.fragment)
                    fragmentStates.getOrPut(op.fragment.name) { FragmentState(op.fragment) }
                }
                is TransactionOp.Remove -> {
                    for (container in containers.values) container.remove(op.fragment)
                    fragmentStates.remove(op.fragment.name)
                }
                is TransactionOp.Hide -> {
                    fragmentStates[op.fragment.name]?.hidden = true
                }
                is TransactionOp.Show -> {
                    fragmentStates[op.fragment.name]?.hidden = false
                }
                is TransactionOp.Detach -> {
                    for (c in containers.values) c.remove(op.fragment)
                    fragmentStates[op.fragment.name]?.detached = true
                }
                is TransactionOp.Attach -> {
                    fragmentStates[op.fragment.name]?.detached = false
                    val lc = fragmentStates[op.fragment.name]?.lastContainer
                    if (lc != null) {
                        containers.getOrPut(lc) { Container(lc) }.add(op.fragment)
                    }
                }
                is TransactionOp.SetMax -> {
                    fragmentStates[op.fragment.name]?.maxLifecycle = op.maxState
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
