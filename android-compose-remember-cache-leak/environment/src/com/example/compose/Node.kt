
package com.example.compose

data class ComposeNode(
    val id: String,
    var parent: String?,
    var key: String,
    val viewModel: MutableMap<String, String> = mutableMapOf(),
    val remember: MutableMap<String, String> = mutableMapOf(),
    val saved: MutableMap<String, String> = mutableMapOf(),
    val children: MutableSet<String> = mutableSetOf(),
    var hidden: Boolean = false
)
