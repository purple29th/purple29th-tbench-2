package com.example.lease

data class Lease(
    val resource: String,
    var holder: String?,
    var fencing: Long,
    var deadlineMs: Long,
)
