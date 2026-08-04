
package com.example.compose

class ComposeManager {
    private val nodes = mutableMapOf<String, ComposeNode>()

    fun mount(id: String, parent: String, key: String) {
        if (nodes.containsKey(id)) return
        // BUG: does not check parent existence properly and does not add to parent children correctly for edge case
        if (parent != "NONE" && !nodes.containsKey(parent)) {
            // buggy: should ignore but also should not create, we ignore correctly here, but later unmount fails to clear children
            return
        }
        val parentVal = if (parent == "NONE") null else parent
        val node = ComposeNode(id, parentVal, key)
        nodes[id] = node
        if (parentVal != null) {
            nodes[parentVal]?.children?.add(id)
        }
    }

    fun updateKey(id: String, newKey: String) {
        val node = nodes[id] ?: return
        if (node.key == newKey) return
        // BUG: only clears remember for self, not descendants, and leaks
        node.remember.clear()
        node.key = newKey
        // missing recursive clear for children
    }

    fun vmPut(id: String, k: String, v: String) {
        nodes[id]?.viewModel?.put(k, v)
    }

    fun rememberPut(id: String, k: String, v: String) {
        nodes[id]?.remember?.put(k, v)
    }

    fun unmount(id: String) {
        val node = nodes[id] ?: return
        // BUG: only removes self, not descendants, leaks children viewModel and remember
        val parent = node.parent
        if (parent != null) {
            nodes[parent]?.children?.remove(id)
        }
        nodes.remove(id)
        // missing recursive removal of children
    }

    fun snapshot(): String {
        if (nodes.isEmpty()) return ""
        val sb = StringBuilder()
        for (nid in nodes.keys.sorted()) {
            val n = nodes[nid]!!
            val parentStr = n.parent ?: "NONE"
            val vmStr = n.viewModel.entries.sortedBy { it.key }.joinToString(",") { "${it.key}=${it.value}" }
            val remStr = n.remember.entries.sortedBy { it.key }.joinToString(",") { "${it.key}=${it.value}" }
            val childrenStr = n.children.sorted().joinToString(",")
            sb.append("node=$nid parent=$parentStr key=${n.key} viewModel={$vmStr} remember={$remStr} children=[$childrenStr]\n")
        }
        return sb.toString().trimEnd()
    }

    fun snapshotBlocks(): List<String> {
        // not used, Main handles blocks
        return listOf(snapshot())
    }
}
