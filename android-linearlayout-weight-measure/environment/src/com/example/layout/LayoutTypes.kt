package com.example.layout

enum class ChildKind { FIXED, WRAP, WEIGHT }

class Child(
    val id: String,
    val kind: ChildKind,
    val value: Int,
    val margin: Int,
) {
    var measured: Int = 0
    var start: Int = 0

    fun spec(): String = "$kind($value)"
}
