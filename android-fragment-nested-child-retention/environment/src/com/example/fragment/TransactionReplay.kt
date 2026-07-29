package com.example.fragment

object TransactionReplay {
    fun replayInto(
        containers: MutableMap<String, Container>,
        fragmentStates: MutableMap<String, FragmentState>,
        ops: List<TransactionOp>
    ) {
        // BUG: ignores child fragment validation and hide/show lifecycle
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
                    // BUG: parent may not exist after rotate if not backstacked
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

    // Old signature used by buggy FragmentManager.rotate()
    fun replayInto(containers: MutableMap<String, Container>, ops: List<TransactionOp>) {
        // This overload is intentionally buggy for rotate path
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
