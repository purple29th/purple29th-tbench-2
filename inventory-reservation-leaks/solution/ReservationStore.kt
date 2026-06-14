package com.example.inventory

class ReservationStore(private val inventory: Inventory) {
    private val byOrder = mutableMapOf<String, Reservation>()

    fun reserve(orderId: String, sku: String, qty: Int, expiresAtMs: Long): Boolean {
        if (orderId in byOrder) return false
        if (!inventory.tryReserve(sku, qty)) return false
        byOrder[orderId] = Reservation(orderId, sku, qty, expiresAtMs)
        return true
    }

    fun commit(orderId: String): Boolean = withPending(orderId) { reservation ->
        inventory.finalize(reservation.sku, reservation.qty)
        reservation.state = ReservationState.COMMITTED
    }

    fun cancel(orderId: String): Boolean = withPending(orderId) { reservation ->
        inventory.release(reservation.sku, reservation.qty)
        reservation.state = ReservationState.CANCELLED
    }

    fun tick(nowMs: Long) {
        for (reservation in byOrder.values) {
            if (reservation.state != ReservationState.PENDING) continue
            if (reservation.expiresAtMs > nowMs) continue
            inventory.release(reservation.sku, reservation.qty)
            reservation.state = ReservationState.EXPIRED
        }
    }

    private inline fun withPending(orderId: String, action: (Reservation) -> Unit): Boolean {
        val reservation = byOrder[orderId] ?: return false
        if (reservation.state != ReservationState.PENDING) return false
        action(reservation)
        return true
    }
}
