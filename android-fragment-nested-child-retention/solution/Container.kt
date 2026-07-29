package com.example.fragment

class Container(val id: String) {
    private val fragments = mutableListOf<Fragment>()

    fun add(fragment: Fragment) {
        if (fragments.none { it.name == fragment.name }) {
            fragments.add(fragment)
        }
    }

    fun replace(fragment: Fragment): List<Fragment> {
        val previous = fragments.toList()
        fragments.clear()
        fragments.add(fragment)
        return previous
    }

    fun remove(fragment: Fragment): Boolean {
        return fragments.removeAll { it.name == fragment.name }
    }

    fun removeByName(name: String): Boolean {
        return fragments.removeAll { it.name == name }
    }

    fun isEmpty(): Boolean = fragments.isEmpty()

    fun snapshot(): List<Fragment> = fragments.toList()

    fun clear() { fragments.clear() }
}
