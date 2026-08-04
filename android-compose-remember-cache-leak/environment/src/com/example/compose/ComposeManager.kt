
package com.example.compose

class ComposeManager {
    private val nodes = mutableMapOf<String, ComposeNode>()
    private val txns = mutableMapOf<String, MutableList<TxnOp>>()
    private val backstackNames = mutableMapOf<String, String>()
    private val backstack = mutableListOf<Pair<String, Map<String, ComposeNode>>>()

    private sealed class TxnOp {
        data class Mount(val id: String, val parent: String, val key: String): TxnOp()
        data class UpdateKey(val id: String, val newKey: String): TxnOp()
        data class Hide(val id: String): TxnOp()
        data class Show(val id: String): TxnOp()
        data class Unmount(val id: String): TxnOp()
    }

    fun begin(tid: String) {
        if (!txns.containsKey(tid)) txns[tid] = mutableListOf()
    }

    fun addToBackstack(tid: String, name: String) {
        backstackNames[tid] = name
    }

    fun mount(tid: String, id: String, parent: String, key: String) {
        txns[tid]?.add(TxnOp.Mount(id, parent, key))
    }

    fun updateKey(tid: String, id: String, newKey: String) {
        txns[tid]?.add(TxnOp.UpdateKey(id, newKey))
    }

    fun hide(tid: String, id: String) {
        txns[tid]?.add(TxnOp.Hide(id))
    }

    fun show(tid: String, id: String) {
        txns[tid]?.add(TxnOp.Show(id))
    }

    fun unmount(tid: String, id: String) {
        txns[tid]?.add(TxnOp.Unmount(id))
    }

    fun vmPut(id: String, k: String, v: String) {
        nodes[id]?.viewModel?.put(k, v)
    }
    fun rememberPut(id: String, k: String, v: String) {
        nodes[id]?.remember?.put(k, v)
    }
    fun savePut(id: String, k: String, v: String) {
        nodes[id]?.saved?.put(k, v)
    }

    fun commit(tid: String) {
        val ops = txns.remove(tid) ?: return
        val name = backstackNames.remove(tid)
        if (name != null) {
                val snap = deepCopy(nodes)
            backstack.add(Pair(name, snap))
        }
        for (op in ops) {
            when (op) {
                is TxnOp.Mount -> {
                    if (nodes.containsKey(op.id)) continue
                    if (op.parent != "NONE" && !nodes.containsKey(op.parent)) continue
                    val p = if (op.parent == "NONE") null else op.parent
                    val node = ComposeNode(op.id, p, op.key)
                    nodes[op.id] = node
                    if (p != null) nodes[p]?.children?.add(op.id)
                }
                is TxnOp.UpdateKey -> {
                    val node = nodes[op.id] ?: continue
                    if (node.key == op.newKey) continue
                    node.remember.clear()
                    node.key = op.newKey
                }
                is TxnOp.Hide -> {
                    val node = nodes[op.id] ?: continue
                    node.remember.clear()
                    node.hidden = true
                }
                is TxnOp.Show -> {
                    val node = nodes[op.id] ?: continue
                    node.hidden = false
                }
                is TxnOp.Unmount -> {
                    val node = nodes[op.id] ?: continue
                    val parent = node.parent
                    if (parent != null) nodes[parent]?.children?.remove(op.id)
                    nodes.remove(op.id)
                }
            }
        }
    }

    fun pop(name: String) {
        if (backstack.isEmpty()) return
        if (name == "NONE" || name.isEmpty()) {
            val (_, snap) = backstack.removeAt(backstack.size - 1)
            nodes.clear()
            nodes.putAll(deepCopy(snap))
            return
        }
        val idx = backstack.indexOfLast { it.first == name }
        if (idx == -1) return
        val (_, snap) = backstack[idx]
        while (backstack.size > idx) backstack.removeAt(backstack.size - 1)
        nodes.clear()
        nodes.putAll(deepCopy(snap))
    }

    fun rotate() {
        for (n in nodes.values) {
            n.remember.clear()
        }
    }

    private fun deepCopy(src: Map<String, ComposeNode>): Map<String, ComposeNode> {
        val copy = mutableMapOf<String, ComposeNode>()
        for ((id, node) in src) {
            val newNode = ComposeNode(
                id = node.id,
                parent = node.parent,
                key = node.key,
                viewModel = node.viewModel.toMutableMap(),
                remember = node.remember.toMutableMap(),
                saved = node.saved.toMutableMap(),
                children = node.children.toMutableSet()
            )
            newNode.hidden = node.hidden
            copy[id] = newNode
        }
        return copy
    }

    fun snapshot(): String {
        if (nodes.isEmpty()) return ""
        val sb = StringBuilder()
        for (nid in nodes.keys.sorted()) {
            val n = nodes[nid]!!
            val parentStr = n.parent ?: "NONE"
            val vmStr = n.viewModel.entries.sortedBy { it.key }.joinToString(",") { "${it.key}=${it.value}" }
            val remStr = n.remember.entries.sortedBy { it.key }.joinToString(",") { "${it.key}=${it.value}" }
            val savedStr = n.saved.entries.sortedBy { it.key }.joinToString(",") { "${it.key}=${it.value}" }
            val childrenStr = n.children.sorted().joinToString(",")
            val hiddenStr = if (n.hidden) " hidden" else ""
            sb.append("node=$nid parent=$parentStr key=${n.key} viewModel={$vmStr} remember={$remStr} saved={$savedStr} children=[$childrenStr]$hiddenStr\n")
        }
        return sb.toString().trimEnd()
    }
}
