# Setting

This project simulates a warehouse with stock, reservations, commits, cancels, and time-based expiry. The implementation is buggy: reservations leak, double-commits succeed, and cancels of finalized orders refund stock that's already sold.

# Input operations (/app/scenario.txt)

The driver reads one operation per line:

- STOCK <sku> <qty> — add qty units of <sku> to available stock.
- RESERVE <orderId> <sku> <qty> <expiresAtMs> — reserve qty units of <sku> for <orderId>, expiring at <expiresAtMs>. Fails (no state change) if available stock is insufficient. Fails if <orderId> already has a reservation.
- COMMIT <orderId> — convert the order's reservation from reserved to sold. Only valid for PENDING reservations; no-op for any other state (already committed, cancelled, or expired).
- CANCEL <orderId> — return the order's reserved qty to available. Only valid for PENDING reservations; no-op for any other state.
- TICK <nowMs> — advance time. Every PENDING reservation whose expiresAtMs <= nowMs becomes EXPIRED and its qty returns to available stock.
- QUERY — append the current inventory snapshot to /app/output.txt.

# Inventory state

Each SKU tracks three counts:
- available — unallocated stock, free to reserve
- reserved — held by PENDING reservations
- sold — finalized via COMMIT, no longer available

Invariant: every unit of stock added by STOCK must always be in exactly one of the three buckets. The total of (available + reserved + sold) per SKU equals the total qty added by STOCK calls for that SKU.

# Reservation lifecycle

A reservation transitions: PENDING -> COMMITTED on commit, PENDING -> CANCELLED on cancel, PENDING -> EXPIRED on tick past expiry. Once it leaves PENDING, no further state change is allowed — subsequent commit/cancel are no-ops.

# Output format

On each QUERY, append:

  inventory:
    sku=<name> available=<n> reserved=<n> sold=<n>
    ...

Sort SKU rows by name ascending. Trailing newline after the last row.

# What you need to do

Fix /app/src/com/example/inventory/ReservationStore.kt so that the four lifecycle methods (reserve, commit, cancel, tick) maintain the invariants above.

Do not modify Inventory.kt, Main.kt, Reservation.kt, or ReservationState.kt. The verifier compiles and runs your fixed code automatically — you only need to edit ReservationStore.kt.

# Reference build command (for local debugging only)

  cd /app
  kotlinc src/com/example/inventory/*.kt -include-runtime -d /app/sim.jar
  java -jar /app/sim.jar

The driver reads /app/scenario.txt and writes /app/output.txt.
