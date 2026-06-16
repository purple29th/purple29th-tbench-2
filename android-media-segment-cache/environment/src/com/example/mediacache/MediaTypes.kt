package com.example.mediacache

data class SegmentSpec(val track: String, val durMs: Int, val bitrate: Int) {
    val bytes: Int get() = durMs * bitrate / 8
}

data class MemEntry(
    val key: String,
    val spec: SegmentSpec,
    var lastAccess: Long,
)

data class DiskEntry(
    val key: String,
    val spec: SegmentSpec,
    val lastAccess: Long,
)
