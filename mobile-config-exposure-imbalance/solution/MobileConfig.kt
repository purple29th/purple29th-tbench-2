package com.example.config

private const val DEFAULT_VARIANT = "control"
private const val EMPTY_LOG = "exposures=[]\n"

class MobileConfig(
    private val sessions: SessionTracker,
    private val cache: ExposureCache,
) {
    private val variants = mutableMapOf<UserConfigKey, String>()
    private val overrides = mutableMapOf<UserConfigKey, String>()
    private val emitted = mutableListOf<ExposureEvent>()

    fun read(user: String, config: String, param: String, branch: String) {
        emit(user, config, param)
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

    fun snapshot(): String = if (emitted.isEmpty()) EMPTY_LOG else formatLog(emitted)

    private fun emit(user: String, config: String, param: String) {
        val session = sessions.current(user) ?: return
        if (!cache.shouldLog(user, session, config, param)) return
        val key = UserConfigKey(user, config)
        emitted += ExposureEvent(
            user = user,
            config = config,
            variant = resolveVariant(key),
            session = session,
            overridden = key in overrides,
        )
    }

    private fun resolveVariant(key: UserConfigKey): String =
        overrides[key] ?: variants[key] ?: DEFAULT_VARIANT
}

internal data class UserConfigKey(val user: String, val config: String)

private fun formatLog(events: List<ExposureEvent>): String =
    events.joinToString(prefix = "exposures=[\n", separator = ",\n", postfix = "\n]\n") { "  ${it.render()}" }
