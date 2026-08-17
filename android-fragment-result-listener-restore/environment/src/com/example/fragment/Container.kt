package com.example.fragment

class Container(val id: String) {
    private val fragments = mutableListOf<Fragment>()
    fun add(f: Fragment) { if (fragments.none { it.name == f.name }) fragments.add(f) }
    fun remove(f: Fragment) { fragments.removeAll { it.name == f.name } }
    fun replace(f: Fragment) { fragments.clear(); fragments.add(f) }
    fun clear() { fragments.clear() }
    fun snapshot(): List<Fragment> = fragments.toList()
}
