package com.example.concurrency

enum class JobType { NORMAL, SUPERVISOR }

enum class JobState { ACTIVE, COMPLETING, COMPLETED, CANCELLED, FAILED }

class Job(
    val id: String,
    val parentId: String,
    val type: JobType,
) {
    var state: JobState = JobState.ACTIVE
    var seq: Int = 0
    val children: MutableList<String> = mutableListOf()

    fun isTerminal(): Boolean =
        state == JobState.COMPLETED || state == JobState.CANCELLED || state == JobState.FAILED

    fun isSupervisor(): Boolean = type == JobType.SUPERVISOR
}
