package com.example.choreographer

enum class Phase { INPUT, ANIMATION, INSETS, TRAVERSAL }

enum class Repeat { ONCE, REPEAT }

enum class MessagePriority { SYNC, ASYNC }

data class FrameCallback(
    val token: String,
    val phase: Phase,
    val costMs: Int,
    val repeat: Repeat,
    val sequence: Long,
)

data class InputEvent(val eventTime: Int, val x: Int, val y: Int)

data class QueuedMessage(val priority: MessagePriority, val costMs: Int)

data class FrameRecord(
    val frame: Int,
    val vsyncTime: Int,
    val deadlineMs: Int,
    val spentMs: Int,
    val jank: Boolean,
    val phaseRosters: Map<Phase, List<String>>,
)
