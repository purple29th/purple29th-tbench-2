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
