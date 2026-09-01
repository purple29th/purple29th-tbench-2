package com.example.grpc

private const val INITIAL_CONNECTION_WINDOW = 65535
private const val INITIAL_STREAM_WINDOW = 65535
private const val MIN_WEIGHT = 1
private const val MAX_WEIGHT = 256
private const val CONTROL_STREAM_ID = 0

class StreamMultiplexer {
    private val streams = mutableMapOf<Int, Stream>()
    private val frames = mutableListOf<EmittedFrame>()
    private var connectionWindow: Int = INITIAL_CONNECTION_WINDOW

    fun openStream(streamId: Int, weight: Int) {
        if (streamId == CONTROL_STREAM_ID) return
        if (weight !in MIN_WEIGHT..MAX_WEIGHT) return
        if (streamId in streams) return
        streams[streamId] = Stream(streamId, weight)
    }

    fun sendHeaders(streamId: Int) {
        val stream = streams[streamId] ?: return
        if (stream.state == StreamState.CLOSED) return
        frames += EmittedFrame(FrameType.HEADERS, streamId, 0)
    }

    fun sendData(streamId: Int, bytes: Int, endStream: Boolean) {
        val stream = streams[streamId] ?: return
        if (stream.state == StreamState.CLOSED) return
        if (stream.state == StreamState.HALF_CLOSED_LOCAL) return
        stream.queue += QueuedData(bytes, endStream)
    }

    fun windowUpdate(streamId: Int, increment: Int) {
        if (increment <= 0) return
        if (streamId == CONTROL_STREAM_ID) {
            connectionWindow += increment
            return
        }
        val stream = streams[streamId] ?: return
        if (stream.state == StreamState.HALF_CLOSED_LOCAL) return
        if (stream.state == StreamState.CLOSED) return
        stream.window += increment
    }

    fun resetStream(streamId: Int) {
        val stream = streams[streamId] ?: return
        if (stream.state == StreamState.CLOSED) return
        stream.state = StreamState.CLOSED
        stream.queue.clear()
    }

    fun ackBytes(streamId: Int, bytes: Int) {
        connectionWindow += bytes
    }

    fun halfCloseLocal(streamId: Int) {
        val stream = streams[streamId] ?: return
        if (stream.state != StreamState.OPEN) return
        stream.state = StreamState.HALF_CLOSED_LOCAL
    }

    fun tick() {
        val contenders = streams.values.filter(::canContend).sortedBy { it.id }
        if (contenders.isEmpty()) return
        val winner = contenders.maxByOrNull { it.weight } ?: return
        drain(winner)
    }

    fun snapshot(): String = buildString {
        appendConnection(this)
        appendStreams(this)
        appendFrames(this)
    }

    private fun drain(stream: Stream) {
        while (stream.queue.isNotEmpty()) {
            if (connectionWindow == 0) return
            val head = stream.queue.first()
            val available = minOf(head.bytes, stream.window, connectionWindow)
            if (available == 0) return
            emit(stream, available)
            consume(stream, head, available)
        }
    }

    private fun emit(stream: Stream, bytes: Int) {
        frames += EmittedFrame(FrameType.DATA, stream.id, bytes)
        stream.sent += bytes
        stream.window -= bytes
        connectionWindow -= bytes
    }

    private fun consume(stream: Stream, head: QueuedData, bytes: Int) {
        if (bytes == head.bytes) {
            stream.queue.removeAt(0)
            if (head.endStream) stream.state = StreamState.HALF_CLOSED_LOCAL
        } else {
            stream.queue[0] = head.copy(bytes = head.bytes - bytes)
        }
    }

    private fun canContend(stream: Stream): Boolean =
        stream.queue.isNotEmpty() &&
            stream.window > 0 &&
            (stream.state == StreamState.OPEN || stream.state == StreamState.HALF_CLOSED_LOCAL)

    private fun appendConnection(builder: StringBuilder) {
        builder.append("connection window=$connectionWindow\n")
    }

    private fun appendStreams(builder: StringBuilder) {
        builder.append("streams:\n")
        for (stream in streams.values.sortedBy { it.id }) {
            builder.append("  ${stream.render()}\n")
        }
    }

    private fun appendFrames(builder: StringBuilder) {
        builder.append("frames:\n")
        for (frame in frames) builder.append("  ${frame.render()}\n")
    }

    private class Stream(val id: Int, val weight: Int) {
        var state: StreamState = StreamState.OPEN
        var window: Int = INITIAL_STREAM_WINDOW
        var sent: Int = 0
        val queue: MutableList<QueuedData> = mutableListOf()

        fun queuedBytes(): Int = queue.sumOf { it.bytes }

        fun render(): String {
            val displayedWindow = if (state == StreamState.CLOSED) 0 else window
            return "id=$id state=$state weight=$weight window=$displayedWindow queued=${queuedBytes()} sent=$sent"
        }
    }
}
