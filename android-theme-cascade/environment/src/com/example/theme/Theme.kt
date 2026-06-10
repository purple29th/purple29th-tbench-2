package com.example.theme

class Theme(
    val name: String,
    val parent: Theme?,
    private val ownTokens: TokenMap = TokenMap()
) {
    fun setToken(key: String, value: String) { ownTokens.set(key, value) }
    fun ownTokens(): TokenMap = ownTokens

    fun parentChain(): List<Theme> {
        val chain = mutableListOf<Theme>()
        var current: Theme? = this
        while (current != null) {
            chain.add(0, current)
            current = current.parent
        }
        return chain
    }
}
