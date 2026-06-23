import kotlin.system.exitProcess

private const val ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
private const val RADIX = 32
private const val KEY_LENGTH = 16
private const val MODULUS = 1000003L
private const val TARGET = 192163L
private val COEFFICIENTS = longArrayOf(97L, 89L, 83L, 79L, 73L, 71L, 67L, 61L, 59L, 53L, 47L, 43L, 41L, 37L, 31L, 29L)

private fun decode(raw: String): IntArray? {
    val symbols = raw.uppercase().filter { it != '-' && it != ' ' }
    if (symbols.length != KEY_LENGTH) return null
    val values = IntArray(KEY_LENGTH)
    for (i in symbols.indices) {
        val index = ALPHABET.indexOf(symbols[i])
        if (index < 0) return null
        values[i] = index
    }
    return values
}

// Additive per-position digest: each symbol contributes COEFFICIENTS[i] times
// the cube of its (1-based) value, summed modulo MODULUS.
private fun digest(values: IntArray): Long {
    var accumulator = 0L
    for (i in 0 until KEY_LENGTH) {
        val x = (values[i] + 1).toLong()
        val cube = (x * x * x) % MODULUS
        accumulator = (accumulator + COEFFICIENTS[i] * cube) % MODULUS
    }
    return accumulator
}

private fun accepts(values: IntArray): Boolean = digest(values) == TARGET

private fun readKey(args: Array<String>): String =
    if (args.isNotEmpty()) args[0] else (readLine() ?: "")

fun main(args: Array<String>) {
    val values = decode(readKey(args))
    val valid = values != null && accepts(values)
    println(if (valid) "ACCEPTED" else "REJECTED")
    exitProcess(0)
}
