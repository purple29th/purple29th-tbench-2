package com.example.theme

class Theme(
    val name: String,
    parent: Theme?,
    private val ownTokens: TokenMap = TokenMap()
) {
    // Snapshot the parent's effective tokens (own + ancestor snapshot)
    // at registration time. Later mutations to the parent do not leak through.
    private val parentSnapshot: TokenMap = TokenMap().also { snap ->
        if (parent != null) {
            snap.mergeFrom(parent.parentSnapshot)
            snap.mergeFrom(parent.ownTokens)
        }
    }

    fun setToken(key: String, value: String) { ownTokens.set(key, value) }
    fun ownTokens(): TokenMap = ownTokens
    fun parentSnapshot(): TokenMap = parentSnapshot
}
