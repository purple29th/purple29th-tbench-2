package com.example.inventory

class ReservationStore(private val inventory: Inventory) {
    private val byOrder = mutableMapOf<String, Reservation>()

    fun reserve(orderId: String, sku: String, qty: Int, expiresAtMs: Long): Boolean {
        // BUG: duplicate orderId silently overwrites the previous reservation,
        // orphaning the prior entry in "reserved" with no way to release it.
        if (!inventory.tryReserve(sku, qty)) return false
        byOrder[orderId] = Reservation(orderId, sku, qty, expiresAtMs)
        return true
    }

    fun commit(orderId: String): Boolean {
        // BUG: doesn't validate state — committing an already-committed or
        // expired reservation re-runs finalize() and double-counts the qty.
        val reservation = byOrder[orderId] ?: return false
        inventory.finalize(reservation.sku, reservation.qty)
        reservation.state = ReservationState.COMMITTED
        return true
    }

    fun cancel(orderId: String): Boolean {
        // BUG: doesn't validate state — cancelling a committed reservation
        // refunds qty back to "available" while leaving "sold" inflated.
        val reservation = byOrder[orderId] ?: return false
        inventory.release(reservation.sku, reservation.qty)
        reservation.state = ReservationState.CANCELLED
        return true
    }

    fun tick(nowMs: Long) {
        // BUG: marks expired reservations but never releases their stock —
        // expired qty stays in "reserved" forever.
        for (reservation in byOrder.values) {
            if (reservation.state != ReservationState.PENDING) continue
            if (reservation.expiresAtMs > nowMs) continue
            reservation.state = ReservationState.EXPIRED
        }
    }
}
