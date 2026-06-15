package com.example.bitmappool

enum class BitmapConfig(val bytesPerPixel: Int) {
    ARGB_8888(4),
    RGB_565(2),
    ALPHA_8(1);

    companion object {
        fun fromString(name: String): BitmapConfig =
            values().firstOrNull { it.name == name }
                ?: error("unknown bitmap config: $name")
    }
}

data class BitmapSpec(val width: Int, val height: Int, val config: BitmapConfig) {
    val bytes: Int get() = width * height * config.bytesPerPixel
}

data class StrongEntry(
    val key: String,
    val spec: BitmapSpec,
    var lastAccess: Long,
)

data class SoftEntry(
    val key: String,
    val spec: BitmapSpec,
    val lastAccess: Long,
)
