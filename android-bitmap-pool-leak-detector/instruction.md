# Setting

Simulates an Android BitmapPool like Glide / Coil / Fresco: a scrolling feed allocates Bitmaps for thumbnails, recycles them when scrolled off-screen, and reuses them by (width, height, config). Bugs in this layer either OOM the app under scroll pressure or crash mid-render with IllegalStateException: Cannot draw recycled bitmap.

The current implementation in /app/src/com/example/bitmappool/BitmapPool.kt produces wrong output across several scenarios. Fix it.

# Operations (/app/scenario.txt)

- ALLOC <key> <width> <height> <config> — allocate a fresh bitmap. config is one of ARGB_8888, RGB_565, ALPHA_8. The bitmap counts toward strong-tier bytes immediately and may itself trigger eviction.
- BEGIN_DRAW <key> — increment the active-draw depth counter for <key>.
- END_DRAW <key> — decrement the active-draw depth counter for <key> (remove from active set when it reaches 0).
- RECYCLE <key> — return the bitmap to the pool. If the active-draw depth is greater than zero, drop the bitmap entirely (see leak section); otherwise the entry stays in the strong tier and its lastAccess is updated.
- ACQUIRE <key> <width> <height> <config> — reuse a pool entry whose (width, height, config) match exactly, or allocate fresh if none match. Search order: strong tier, then soft tier, then fresh allocate. The acquired bitmap is keyed under the new <key>.
- GC — clear the soft tier entirely. The strong tier and the active-draw set are untouched.
- QUERY — append a snapshot to /app/output.txt.

# Bytes per pixel

ARGB_8888 = 4, RGB_565 = 2, ALPHA_8 = 1. A bitmap's bytes are width * height * bytesPerPixel(config). The cap is maxSizeBytes = 32768. Only the strong tier counts toward the cap.

# Tick / lastAccess

A monotonic currentTick counter increments by 1 on every input op except QUERY. Each strong-tier entry tracks lastAccess. lastAccess is set on ALLOC and on the fresh-allocate path of ACQUIRE, and refreshed on RECYCLE that returns the entry to the pool. REUSE_STRONG and REUSE_SOFT do not refresh lastAccess — they preserve the entry's existing value (REUSE_SOFT preserves the value the entry had at the moment it was demoted to soft).

# Tiers and reuse

The pool has two tiers:

- Strong tier. LRU-ordered, byte-accounted toward maxSizeBytes. The lookup target for ACQUIRE.
- Soft tier. A flat list. Not byte-accounted. Cleared only by GC.

ACQUIRE:

- Strong-tier exact match: emit REUSE_STRONG <new_key>. The matched entry's old key is removed; the entry is re-stored under <new_key>. The entry's lastAccess is preserved from the original entry — REUSE_STRONG does not refresh it.
- Soft-tier exact match (only checked if strong missed): emit REUSE_SOFT <new_key>. The entry is removed from the soft tier and promoted to the strong tier under <new_key> with current-tick lastAccess. Its bytes are re-added to the strong-tier total, which may itself trigger eviction inside the same ACQUIRE call.
- No match in either tier: allocate fresh. Emit ALLOC <new_key>. The new bytes are added to the strong-tier total, which may trigger eviction.

Exact match means all three of width, height, and config are equal. A pooled ARGB_8888 entry cannot satisfy a request for RGB_565 even at the same dimensions.

# Eviction

Eviction is strong-tier only and runs whenever the strong-tier byte total exceeds maxSizeBytes. The pool repeatedly removes one entry until the total fits at or below the cap.

The victim is chosen as follows:

- Smallest lastAccess wins.
- If two entries share the smallest lastAccess, the one with smaller bytes is evicted first.

Each evicted entry emits one event:

- EVICT <key> reason=lru — chosen on lastAccess alone.
- EVICT <key> reason=tie — chosen via the bytes tie-break.

Evicted entries are demoted to the soft tier under their existing key. They are not destroyed.

# Active-draw and leak detection

BEGIN_DRAW <key> and END_DRAW <key> maintain a per-key depth counter. The active-draw set lists keys whose depth is greater than zero.

If RECYCLE <key> is called while the active-draw depth for <key> is greater than zero:

- Emit LEAK <key>.
- Subtract the bitmap's bytes from the strong-tier byte total.
- Remove the bitmap record from the strong tier.
- Remove the key from the active-draw set.

After a leak, subsequent END_DRAW <key> calls are silent no-ops (the key is no longer tracked).

# Recycle deduplication

When RECYCLE <key> succeeds (the bitmap was not in active draw and stays in the strong tier), the pool then checks whether any other strong-tier entry has the same (width, height, config) as the recycled bitmap. If one exists, that other entry is removed from the strong tier, demoted to the soft tier, and a DEDUP <other_key> event is emitted. The recycled bitmap itself stays in the strong tier under its own key.

Only one duplicate is removed per RECYCLE. If multiple duplicates exist, the one returned first by iteration order over the strong tier is chosen.

# GC

GC removes every entry in the soft tier and emits GC cleared=<n> where <n> is the number of entries removed. The strong tier and active-draw set are not affected.

# Silent no-ops

BEGIN_DRAW, END_DRAW, and RECYCLE on a key that is not currently in the strong tier produce no event. They still advance currentTick.

# Output format

Each QUERY appends a snapshot:

  pool maxBytes=32768 currentBytes=<n>
  strong:
    key=<k> w=<w> h=<h> config=<C> bytes=<n> lastAccess=<tick>
    ...
  soft:
    key=<k> w=<w> h=<h> config=<C> bytes=<n>
    ...
  active:
    key=<k> depth=<n>
    ...
  events:
    <event>
    ...

- currentBytes is the sum of strong-tier bytes only.
- strong: rows are sorted by key ascending. Each row carries lastAccess.
- soft: rows are sorted by key ascending. No lastAccess.
- active: rows are sorted by key ascending. Only keys with depth > 0 are listed.
- events: is the cumulative log of every emitted event in emission order: ALLOC <key>, EVICT <key> reason=<lru|tie>, REUSE_STRONG <key>, REUSE_SOFT <key>, LEAK <key>, DEDUP <key>, GC cleared=<n>.

# What you need to do

Fix /app/src/com/example/bitmappool/BitmapPool.kt. Do not modify Main.kt or BitmapTypes.kt. The verifier compiles and runs your fixed code automatically.

# Reference build (local debugging only)

  cd /app
  kotlinc src/com/example/bitmappool/*.kt -include-runtime -d /app/sim.jar
  java -jar /app/sim.jar scenario.txt output.txt

The driver reads the scenario path from the first argument (default /app/scenario.txt) and writes to the second (default /app/output.txt).
