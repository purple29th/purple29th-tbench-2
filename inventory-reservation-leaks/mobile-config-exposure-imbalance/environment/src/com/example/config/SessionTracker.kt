package com.example.config

class SessionTracker {
    private val activeSessionByUser = mutableMapOf<String, Int>()
    private val sessionCountByUser = mutableMapOf<String, Int>()

    fun start(user: String) {
        if (user in activeSessionByUser) return
        val next = (sessionCountByUser[user] ?: 0) + 1
        sessionCountByUser[user] = next
        activeSessionByUser[user] = next
    }

    fun end(user: String) { activeSessionByUser.remove(user) }

    fun current(user: String): Int? = activeSessionByUser[user]
}
