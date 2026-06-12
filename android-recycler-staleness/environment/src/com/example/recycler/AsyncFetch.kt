package com.example.recycler

data class AsyncFetch(
    val sequence: Long,
    val cellId: String,
    val itemId: String,
    val expectedToken: Long,
    val dueAt: Long
)
