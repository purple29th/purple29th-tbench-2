package com.example.concurrency

private const val ROOT_ID = "root"

class StructuredScope {
    private val jobs = linkedMapOf<String, Job>()
    private val rootChildren = mutableListOf<String>()
    private val events = mutableListOf<String>()

    fun launch(id: String, parentId: String, type: JobType) {
        if (id in jobs) return
        val job = Job(id, parentId, type)
        jobs[id] = job
        registerChild(parentId, id)
        events += "STARTED $id"
    }

    fun complete(id: String) {
        val job = jobs[id] ?: return
        if (job.isTerminal()) return
        job.state = JobState.COMPLETED
        events += "COMPLETED $id"
    }

    fun await(id: String) {
        val job = jobs[id] ?: return
        if (job.isTerminal()) return
        job.state = JobState.COMPLETED
        events += "COMPLETED $id"
    }

    fun fail(id: String) {
        val job = jobs[id] ?: return
        if (job.isTerminal()) return
        job.state = JobState.FAILED
        events += "FAILED $id"
        propagateFailure(job.parentId)
    }

    fun cancel(id: String) {
        val job = jobs[id] ?: return
        if (job.isTerminal()) return
        job.state = JobState.CANCELLED
        events += "CANCELLED ${job.id}"
    }

    fun snapshot(): String = buildString {
        appendJobs(this)
        appendEvents(this)
    }

    private fun propagateFailure(parentId: String) {
        if (parentId == ROOT_ID) return
        val parent = jobs[parentId] ?: return
        if (!parent.isTerminal()) {
            parent.state = JobState.CANCELLED
            events += "CANCELLED ${parent.id}"
        }
        propagateFailure(parent.parentId)
    }

    private fun cancelTree(job: Job) {
        if (job.isTerminal()) return
        job.state = JobState.CANCELLED
        events += "CANCELLED ${job.id}"
        for (childId in job.children.toList()) {
            jobs[childId]?.let { cancelTree(it) }
        }
    }

    private fun registerChild(parentId: String, childId: String) {
        if (parentId == ROOT_ID) {
            rootChildren += childId
        } else {
            jobs[parentId]?.children?.add(childId)
        }
    }

    private fun appendJobs(builder: StringBuilder) {
        builder.append("jobs:\n")
        for (job in jobs.values.sortedBy { it.id }) {
            builder.append("  id=${job.id} parent=${job.parentId} ")
            builder.append("type=${typeLabel(job.type)} state=${job.state} seq=${job.seq}\n")
        }
    }

    private fun appendEvents(builder: StringBuilder) {
        builder.append("events:\n")
        for (event in events) builder.append("  $event\n")
    }

    private fun typeLabel(type: JobType): String = when (type) {
        JobType.NORMAL -> "normal"
        JobType.SUPERVISOR -> "supervisor"
    }
}
