package com.example.inventory

data class Reservation(
    val orderId: String,
    val sku: String,
    val qty: Int,
    val expiresAtMs: Long,
    var state: ReservationState = ReservationState.PENDING,
)
