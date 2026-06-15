package com.example.grpc

enum class FrameType { HEADERS, DATA }

data class EmittedFrame(val type: FrameType, val streamId: Int, val bytes: Int) {
    fun render(): String = "$type stream=$streamId bytes=$bytes"
}

data class QueuedData(
    val bytes: Int,
    val endStream: Boolean,
)
