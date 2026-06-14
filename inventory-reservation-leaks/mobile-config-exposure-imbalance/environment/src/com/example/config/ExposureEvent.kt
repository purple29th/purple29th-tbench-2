package com.example.config

data class ExposureEvent(
    val user: String,
    val config: String,
    val variant: String,
    val session: Int,
    val overridden: Boolean,
) {
    fun render(): String =
        "user=$user config=$config variant=$variant session=$session overridden=$overridden"
}
