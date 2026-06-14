package com.example.lease

class LeaseManager {
    private val leases = mutableMapOf<String, Lease>()

    fun acquire(client: String, resource: String, ttlMs: Long, nowMs: Long): Boolean {
        val lease = leaseFor(resource)
        if (lease.holder != null) return false
        lease.fencing += 1
        lease.holder = client
        lease.deadlineMs = nowMs + ttlMs
        return true
    }

    fun renew(client: String, resource: String, newTtlMs: Long, nowMs: Long): Boolean {
        val lease = leases[resource] ?: return false
        if (lease.holder != client) return false
        lease.deadlineMs = nowMs + newTtlMs
        lease.fencing += 1
        return true
    }

    fun release(client: String, resource: String, nowMs: Long): Boolean {
        val lease = leases[resource] ?: return false
        if (lease.holder != client) return false
        lease.fencing = 0
        lease.holder = null
        lease.deadlineMs = 0
        return true
    }

    fun transfer(from: String, to: String, resource: String, nowMs: Long): Boolean {
        val lease = leases[resource] ?: return false
        if (lease.holder != from) return false
        lease.fencing += 1
        lease.holder = to
        return true
    }

    fun tick(nowMs: Long) {
        for (lease in leases.values) {
            if (lease.holder == null) continue
            if (lease.deadlineMs < nowMs) {
                lease.holder = null
                lease.deadlineMs = 0
                lease.fencing = 0
            }
        }
    }

    fun snapshot(): String = buildString {
        append("resources:\n")
        for (resource in leases.keys.sorted()) {
            val lease = leases.getValue(resource)
            if (lease.holder == null) {
                append("  resource=$resource free fencing=${lease.fencing}\n")
            } else {
                append("  resource=$resource holder=${lease.holder} fencing=${lease.fencing} deadline=${lease.deadlineMs}\n")
            }
        }
    }

    private fun leaseFor(resource: String): Lease =
        leases.getOrPut(resource) { Lease(resource, holder = null, fencing = 0, deadlineMs = 0) }
}
