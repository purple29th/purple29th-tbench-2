package com.example.config

private const val DEFAULT_VARIANT = "control"
private const val EMPTY_LOG = "exposures=[]\n"

class MobileConfig(
    private val sessions: SessionTracker,
    private val cache: ExposureCache,
) {
    private val variants = mutableMapOf<UserConfigKey, String>()
    private val overrides = mutableMapOf<UserConfigKey, String>()
    private val priorities = mutableMapOf<String, Int>()
    private val fatigue = mutableMapOf<String, Int>()
    private val pending = mutableListOf<Pending>()
    private val logged = mutableListOf<ExposureEvent>()
    private var budget: Long = 0
    private var arrivalSeq: Long = 0

    fun read(user: String, config: String, param: String, branch: String) {
        val session = sessions.current(user) ?: return
        if (!cache.shouldLog(user, session, config, param)) return
        val key = UserConfigKey(user, config)
        pending += Pending(
            ExposureEvent(
                user = user,
                config = config,
                variant = resolveVariant(key),
                session = session,
                overridden = key in overrides,
            ),
            config,
            arrivalSeq++,
        )
    }

    fun defaultRead(user: String, config: String, param: String) {}

    fun variantFlip(user: String, config: String, newVariant: String) {
        variants[UserConfigKey(user, config)] = newVariant
        val session = sessions.current(user) ?: return
        cache.invalidate(user, session, config)
    }

    fun override(user: String, config: String, variant: String) {
        overrides[UserConfigKey(user, config)] = variant
    }

    fun grant(amount: Long) { budget += amount }

    fun priority(config: String, value: Int) { priorities[config] = value }

    fun flush() {
        val ordered = pending.sortedWith(
            compareByDescending<Pending> { (priorities[it.config] ?: 0) - (fatigue[it.config] ?: 0) }
                .thenBy { it.seq }
        )
        val remaining = mutableListOf<Pending>()
        for (p in ordered) {
            if (budget >= 1) {
                budget -= 1
                logged += p.event
                fatigue[p.config] = (fatigue[p.config] ?: 0) + 1
            } else {
                remaining += p
            }
        }
        pending.clear()
        pending.addAll(remaining)
    }

    fun snapshot(): String = if (logged.isEmpty()) EMPTY_LOG else formatLog(logged)

    private fun resolveVariant(key: UserConfigKey): String =
        overrides[key] ?: variants[key] ?: DEFAULT_VARIANT

    private data class Pending(val event: ExposureEvent, val config: String, val seq: Long)
}

internal data class UserConfigKey(val user: String, val config: String)

private fun formatLog(events: List<ExposureEvent>): String =
    events.joinToString(prefix = "exposures=[\n", separator = ",\n", postfix = "\n]\n") { "  ${it.render()}" }
