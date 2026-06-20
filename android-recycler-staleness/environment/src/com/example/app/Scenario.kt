package com.example.app

sealed class Op {
    data class Bind(val cellId: String, val itemId: String, val title: String, val fetchAt: Long) : Op()
    data class Recycle(val cellId: String) : Op()
    data class Resolve(val itemId: String, val imageUrl: String) : Op()
    data class Tick(val now: Long) : Op()
    data class Query(val cellId: String) : Op()
    data class Refetch(val cellId: String, val fetchAt: Long) : Op()
}

data class Scenario(val ops: List<Op>)
