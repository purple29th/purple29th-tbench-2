package com.example.choreographer

private const val DEFAULT_VSYNC_HZ = 60
private const val RESAMPLE_OFFSET_MS = 4

private val FRAME_INTERVAL_BY_HZ: Map<Int, Int> = mapOf(60 to 16, 90 to 11, 120 to 8)

class DoFrameScheduler {
    private val pendingInputs = mutableListOf<InputEvent>()
    private val syncQueue = ArrayDeque<QueuedMessage>()
    private val asyncQueue = ArrayDeque<QueuedMessage>()
    private val nextFrameCallbacks = mutableListOf<FrameCallback>()
    private val frames = mutableListOf<FrameRecord>()
    private val events = mutableListOf<String>()

    private var sequenceCounter: Long = 0L
    private var vsyncHz: Int = DEFAULT_VSYNC_HZ
    private var pendingVsyncHz: Int? = null
    private var hasSyncBarrier: Boolean = false
    private var currentTime: Int = 0
    private var frameCounter: Int = 0

    fun setVsyncRate(hz: Int) {
        events += "VSYNC_RATE_CHANGED from=$vsyncHz to=$hz"
        pendingVsyncHz = hz
    }

    fun postFrame(token: String, phase: Phase, costMs: Int, repeat: Repeat) {
        nextFrameCallbacks += FrameCallback(token, phase, costMs, repeat, nextSequence())
    }

    fun removeFrame(token: String) {
        nextFrameCallbacks.removeAll { it.token == token }
    }

    fun postInput(eventTime: Int, x: Int, y: Int) {
        pendingInputs += InputEvent(eventTime, x, y)
    }

    fun postMessage(priority: MessagePriority, costMs: Int) {
        queueFor(priority).addLast(QueuedMessage(priority, costMs))
    }

    fun scheduleTraversals() {
        if (hasSyncBarrier) return
        hasSyncBarrier = true
        events += "MSG_BARRIER"
    }

    fun doFrame(vsyncTime: Int) {
        frameCounter += 1
        advanceTimeTo(vsyncTime)
        val frameInterval = currentFrameInterval()
        val deadline = vsyncTime + frameInterval
        val rosters = emptyRosters()

        resampleInput(vsyncTime)
        val frameCallbacks = takeFrameCallbacks()
        runPipeline(frameCallbacks, rosters, deadline)

        val isJank = currentTime > deadline
        if (isJank) emitJank(deadline)

        frames += buildFrameRecord(vsyncTime, deadline, isJank, rosters)
        applyPendingVsyncRate()
    }

    fun drainQueue(budgetMs: Int) {
        var remaining = budgetMs
        while (remaining > 0) {
            val pick = pickMessageForBudget(remaining) ?: break
            dispatchMessage(pick)
            remaining -= pick.costMs
        }
    }

    fun snapshot(): String = buildString {
        appendHeader(this)
        appendFrames(this)
        appendQueue(this)
        appendNextFrameCallbacks(this)
        appendEvents(this)
    }

    private fun runPipeline(
        callbacks: MutableList<FrameCallback>,
        rosters: MutableMap<Phase, MutableList<String>>,
        deadline: Int,
    ) {
        runPhase(Phase.INPUT, callbacks, rosters)
        drainAsyncUntilDeadline(deadline)
        runPhase(Phase.ANIMATION, callbacks, rosters)
        drainAsyncUntilDeadline(deadline)
        runPhase(Phase.INSETS, callbacks, rosters)
        drainAsyncUntilDeadline(deadline)
        liftSyncBarrierIfActive()
        runPhase(Phase.TRAVERSAL, callbacks, rosters)
        drainAnyUntilDeadline(deadline)
    }

    private fun resampleInput(vsyncTime: Int) {
        val cutoff = vsyncTime - RESAMPLE_OFFSET_MS
        val dispatched = pendingInputs.filter { it.eventTime <= cutoff }
        val deferred = pendingInputs.filter { it.eventTime > cutoff }
        if (dispatched.isNotEmpty()) {
            events += "INPUT_BATCH count=${dispatched.size} oldestEventTime=${dispatched.minOf { it.eventTime }}"
        }
        if (deferred.isNotEmpty()) {
            events += "INPUT_DEFERRED count=${deferred.size}"
        }
        pendingInputs.clear()
        pendingInputs.addAll(deferred)
    }

    private fun runPhase(
        phase: Phase,
        callbacks: MutableList<FrameCallback>,
        rosters: MutableMap<Phase, MutableList<String>>,
    ) {
        val phaseCallbacks = callbacks.filter { it.phase == phase }.sortedBy { it.sequence }
        for (callback in phaseCallbacks) executeCallback(callback, rosters)
        callbacks.removeAll(phaseCallbacks)
    }

    private fun executeCallback(
        callback: FrameCallback,
        rosters: MutableMap<Phase, MutableList<String>>,
    ) {
        events += "FRAME_CALLBACK ${callback.token}"
        currentTime += callback.costMs
        rosters.getValue(callback.phase) += callback.token
        if (callback.repeat == Repeat.REPEAT) {
            nextFrameCallbacks += callback.copy(sequence = nextSequence())
        }
    }

    private fun drainAsyncUntilDeadline(deadline: Int) {
        while (currentTime < deadline) {
            val msg = asyncQueue.removeFirstOrNull() ?: return
            dispatchMessage(msg)
        }
    }

    private fun drainAnyUntilDeadline(deadline: Int) {
        while (currentTime < deadline) {
            val pick = pickAsyncOrSync() ?: return
            dispatchMessage(pick)
        }
    }

    private fun pickAsyncOrSync(): QueuedMessage? {
        if (asyncQueue.isNotEmpty()) return asyncQueue.removeFirst()
        if (hasSyncBarrier) return null
        return syncQueue.removeFirstOrNull()
    }

    private fun pickMessageForBudget(remaining: Int): QueuedMessage? {
        val asyncHead = asyncQueue.firstOrNull()
        if (asyncHead != null && asyncHead.costMs <= remaining) return asyncQueue.removeFirst()
        if (hasSyncBarrier) return null
        val syncHead = syncQueue.firstOrNull()
        if (syncHead != null && syncHead.costMs <= remaining) return syncQueue.removeFirst()
        return null
    }

    private fun dispatchMessage(msg: QueuedMessage) {
        currentTime += msg.costMs
        events += "MSG_DISPATCH priority=${priorityLabel(msg.priority)} costMs=${msg.costMs}"
    }

    private fun liftSyncBarrierIfActive() {
        hasSyncBarrier = false
        events += "MSG_BARRIER_LIFTED"
    }

    private fun emitJank(deadline: Int) {
        events += "JANK frame=$frameCounter overrunMs=${currentTime - deadline}"
    }

    private fun advanceTimeTo(target: Int) {
        if (currentTime < target) currentTime = target
    }

    private fun takeFrameCallbacks(): MutableList<FrameCallback> {
        val callbacks = nextFrameCallbacks.toMutableList()
        nextFrameCallbacks.clear()
        return callbacks
    }

    private fun applyPendingVsyncRate() {
        pendingVsyncHz?.let {
            vsyncHz = it
            pendingVsyncHz = null
        }
    }

    private fun nextSequence(): Long {
        sequenceCounter += 1L
        return sequenceCounter
    }

    private fun queueFor(priority: MessagePriority): ArrayDeque<QueuedMessage> = when (priority) {
        MessagePriority.SYNC -> syncQueue
        MessagePriority.ASYNC -> asyncQueue
    }

    private fun currentFrameInterval(): Int =
        FRAME_INTERVAL_BY_HZ[vsyncHz] ?: error("unsupported vsync rate: $vsyncHz")

    private fun priorityLabel(priority: MessagePriority): String = when (priority) {
        MessagePriority.SYNC -> "sync"
        MessagePriority.ASYNC -> "async"
    }

    private fun emptyRosters(): MutableMap<Phase, MutableList<String>> =
        Phase.values().associateWith { mutableListOf<String>() }.toMutableMap()

    private fun buildFrameRecord(
        vsyncTime: Int,
        deadline: Int,
        isJank: Boolean,
        rosters: Map<Phase, MutableList<String>>,
    ): FrameRecord = FrameRecord(
        frame = frameCounter,
        vsyncTime = vsyncTime,
        deadlineMs = deadline,
        spentMs = currentTime - vsyncTime,
        jank = isJank,
        phaseRosters = rosters.mapValues { it.value.toList() },
    )

    private fun appendHeader(builder: StringBuilder) {
        builder.append("vsync rate=$vsyncHz frameIntervalMs=${currentFrameInterval()} currentTime=$currentTime\n")
    }

    private fun appendFrames(builder: StringBuilder) {
        builder.append("frames:\n")
        for (frame in frames) appendFrame(builder, frame)
    }

    private fun appendFrame(builder: StringBuilder, frame: FrameRecord) {
        builder.append("  frame=${frame.frame} vsyncTime=${frame.vsyncTime} ")
        builder.append("deadlineMs=${frame.deadlineMs} spentMs=${frame.spentMs} jank=${frame.jank}\n")
        for (phase in Phase.values()) {
            val tokens = frame.phaseRosters[phase].orEmpty().joinToString(", ")
            builder.append("    ${phase.name}: $tokens\n")
        }
    }

    private fun appendQueue(builder: StringBuilder) {
        val barrierLabel = if (hasSyncBarrier) "active" else "inactive"
        builder.append("queue:\n")
        builder.append("  sync=${syncQueue.size} async=${asyncQueue.size} barrier=$barrierLabel\n")
    }

    private fun appendNextFrameCallbacks(builder: StringBuilder) {
        builder.append("next-frame callbacks:\n")
        val tokens = nextFrameCallbacks.sortedBy { it.sequence }.joinToString(", ") { it.token }
        builder.append("  $tokens\n")
    }

    private fun appendEvents(builder: StringBuilder) {
        builder.append("events:\n")
        for (event in events) builder.append("  $event\n")
    }
}
