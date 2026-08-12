package com.example.fragment

object TransactionReplay {
    fun replayInto(containers: MutableMap<String, Container>, ops: List<TransactionOp>) {
        for (op in ops) {
            when (op) {
                is TransactionOp.Add -> {
                    containers.getOrPut(op.container) { Container(op.container) }.add(op.fragment)
                }
                is TransactionOp.Replace -> {
                    containers.getOrPut(op.container) { Container(op.container) }.replace(op.fragment)
                }
                is TransactionOp.Remove -> {
                    for (c in containers.values) c.remove(op.fragment)
                }
                else -> {}
            }
        }
    }
}
