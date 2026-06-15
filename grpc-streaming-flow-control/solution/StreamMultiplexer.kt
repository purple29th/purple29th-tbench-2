package com.example.grpc

private const val INITIAL_CONNECTION_WINDOW = 65535
private const val INITIAL_STREAM_WINDOW = 65535
private const val MIN_WEIGHT = 1
private const val MAX_WEIGHT = 256
private const val CONTROL_STREAM_ID = 0
private const val CONNECTION_WINDOW_RESERVED_FLOOR = 4096

class StreamMultiplexer {
    private val streams = mutableMapOf<Int, Stream>()
    private val frames = mutableListOf<EmittedFrame>()
    private var connectionWindow: Int = INITIAL_CONNECTION_WINDOW

    fun openStream(streamId: Int, weight: Int) {
        if (!isValidClientStreamId(streamId)) return
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
        if (stream.state != StreamState.OPEN) return
        stream.queue += QueuedData(bytes, endStream)
    }

    fun windowUpdate(streamId: Int, increment: Int) {
        if (increment <= 0) return
        if (streamId == CONTROL_STREAM_ID) {
            connectionWindow += increment
            return
        }
        val stream = streams[streamId] ?: return
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
        if (bytes <= 0) return
        connectionWindow += bytes
    }

    fun halfCloseLocal(streamId: Int) {
        val stream = streams[streamId] ?: return
        if (stream.state != StreamState.OPEN) return
        stream.state = StreamState.HALF_CLOSED_LOCAL
    }

    fun tick() {
        while (drainOnePass()) Unit
    }

    fun snapshot(): String = buildString {
        appendConnection(this)
        appendStreams(this)
        appendFrames(this)
    }

    private fun drainOnePass(): Boolean {
        val contenders = streams.values.filter(::canContend)
        val available = (connectionWindow - CONNECTION_WINDOW_RESERVED_FLOOR).coerceAtLeast(0)
        if (contenders.isEmpty() || available == 0) return false
        val allocations = allocateProportional(contenders, available)
        var emittedAny = false
        for ((stream, allocation) in allocations) {
            val bytesToEmit = minOf(allocation, stream.queuedBytes(), stream.window, connectionWindow)
            if (bytesToEmit == 0) continue
            emitData(stream, bytesToEmit)
            emittedAny = true
        }
        return emittedAny
    }

    private fun allocateProportional(contenders: List<Stream>, available: Int): Map<Stream, Int> {
        val totalWeight = contenders.sumOf { it.weight }
        val baseShares = contenders.associateWith { (available.toLong() * it.weight / totalWeight).toInt() }
        val baseSum = baseShares.values.sum()
        val remainder = available - baseSum
        if (remainder == 0) return baseShares
        val priorityWinner = contenders.sortedWith(compareByDescending<Stream> { it.weight }.thenBy { it.id }).first()
        return baseShares.toMutableMap().also { it[priorityWinner] = (it[priorityWinner] ?: 0) + remainder }
    }

    private fun emitData(stream: Stream, bytes: Int) {
        var remaining = bytes
        while (remaining > 0 && stream.queue.isNotEmpty()) {
            val head = stream.queue.first()
            val take = minOf(remaining, head.bytes)
            recordFrame(stream, take)
            remaining -= take
            if (take == head.bytes) {
                stream.queue.removeAt(0)
                if (head.endStream) stream.state = StreamState.HALF_CLOSED_LOCAL
            } else {
                stream.queue[0] = head.copy(bytes = head.bytes - take)
            }
        }
    }

    private fun recordFrame(stream: Stream, bytes: Int) {
        frames += EmittedFrame(FrameType.DATA, stream.id, bytes)
        stream.sent += bytes
        stream.window -= bytes
        connectionWindow -= bytes
    }

    private fun canContend(stream: Stream): Boolean {
        if (stream.queue.isEmpty()) return false
        if (stream.window <= 0) return false
        return stream.state == StreamState.OPEN || stream.state == StreamState.HALF_CLOSED_LOCAL
    }

    private fun isValidClientStreamId(streamId: Int): Boolean =
        streamId > 0 && streamId % 2 == 1

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
