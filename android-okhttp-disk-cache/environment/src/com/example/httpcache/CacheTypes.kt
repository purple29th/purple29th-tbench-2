package com.example.httpcache

data class ResponseSpec(val url: String, val vary: String, val bytes: Int)

data class MemEntry(
    val key: String,
    val spec: ResponseSpec,
    var lastAccess: Long,
)

data class DiskEntry(
    val key: String,
    val spec: ResponseSpec,
    val lastAccess: Long,
)
