
package com.example.compose

class ComposeManager {
    private val nodes = mutableMapOf<String, ComposeNode>()

    fun mount(id: String, parent: String, key: String) {
        if (nodes.containsKey(id)) return
        if (parent != "NONE" && !nodes.containsKey(parent)) return
        val parentVal = if (parent == "NONE") null else parent
        val node = ComposeNode(id, parentVal, key)
        nodes[id] = node
        if (parentVal != null) {
            nodes[parentVal]?.children?.add(id)
        }
    }

    private fun collectDescendants(rootId: String): Set<String> {
        val result = mutableSetOf<String>()
        val stack = mutableListOf<String>()
        stack.add(rootId)
        while (stack.isNotEmpty()) {
            val cur = stack.removeAt(stack.size - 1)
            if (!nodes.containsKey(cur)) continue
            if (result.contains(cur)) continue
            result.add(cur)
            for (child in nodes[cur]!!.children) {
                stack.add(child)
            }
        }
        return result
    }

    private fun clearRememberRecursive(rootId: String) {
        for (desc in collectDescendants(rootId)) {
            nodes[desc]?.remember?.clear()
        }
    }

    fun updateKey(id: String, newKey: String) {
        val node = nodes[id] ?: return
        if (node.key == newKey) return
        clearRememberRecursive(id)
        node.key = newKey
    }

    fun vmPut(id: String, k: String, v: String) {
        nodes[id]?.viewModel?.put(k, v)
    }

    fun rememberPut(id: String, k: String, v: String) {
        nodes[id]?.remember?.put(k, v)
    }

    fun unmount(id: String) {
        if (!nodes.containsKey(id)) return
        val toRemove = collectDescendants(id)
        // remove from parents that are not themselves being removed
        for (rid in toRemove) {
            val p = nodes[rid]?.parent
            if (p != null && nodes.containsKey(p) && !toRemove.contains(p)) {
                nodes[p]?.children?.remove(rid)
            }
        }
        for (rid in toRemove) {
            nodes.remove(rid)
        }
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
}
