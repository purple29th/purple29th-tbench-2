# Setting

An Android BitmapPool like Glide or Coil. A feed allocates bitmaps, recycles them, and reuses them by width, height, and config. The code in /app/src/com/example/bitmappool/BitmapPool.kt is wrong on several scenarios. Fix it so its QUERY snapshots and event log match.

# Operations (one per line from /app/scenario.txt)

ALLOC key w h config: allocate a fresh bitmap. config is ARGB_8888, RGB_565, or ALPHA_8. It counts toward strong tier bytes right away and may trigger eviction.
BEGIN_DRAW key: add one to the active draw depth for key.
END_DRAW key: subtract one from the active draw depth for key. At zero the key leaves the active set.
RECYCLE key: return the bitmap to the pool. If the active draw depth is above zero it is a leak (see below); otherwise it stays in the strong tier and its lastAccess is refreshed.
ACQUIRE key w h config: reuse a pool entry whose width, height, and config match exactly, or allocate fresh if none match. The result is keyed under the new key.
TOUCH key [key ...]: set the lastAccess of every listed strong tier entry to the current tick, so several entries can share one value. Keys not in the strong tier are ignored. TOUCH emits no event.
GC: clear the whole soft tier. The strong tier and active set are untouched.
QUERY: append a snapshot to /app/output.txt.

# Bytes

bytesPerPixel is 4 for ARGB_8888, 2 for RGB_565, 1 for ALPHA_8. A bitmap is w * h * bytesPerPixel bytes. maxSizeBytes is 32768. Only the strong tier counts toward the cap.

# Tick and lastAccess

currentTick rises by 1 on every operation except QUERY. Each strong entry tracks lastAccess. It is set on ALLOC, on the fresh allocate path of ACQUIRE, on a successful RECYCLE, and on TOUCH. REUSE_STRONG and REUSE_SOFT keep the entry existing lastAccess and never refresh it; for a soft reuse that is the value the entry held when it was demoted to soft.

# Tiers

Strong tier: LRU ordered, byte accounted against the cap, searched first by ACQUIRE. Soft tier: a flat list, not byte accounted, cleared only by GC.

# ACQUIRE

Exact match means equal width, height, and config. Search the strong tier first: on a hit emit REUSE_STRONG new_key, drop the old key, and restore the entry under new_key keeping its lastAccess. If the strong tier missed, search the soft tier: on a hit emit REUSE_SOFT new_key, remove it from soft, and promote it to the strong tier under new_key keeping its demoted lastAccess; its bytes rejoin the strong total and may trigger eviction. If neither tier matches, allocate fresh and emit ALLOC new_key; the new bytes may trigger eviction.

# Eviction

While the strong tier byte total is over the cap, remove one entry at a time until it is at or below the cap. The victim is the entry with the smallest lastAccess. If two entries share the smallest lastAccess, the one with fewer bytes goes first. Emit EVICT key reason=lru when the smallest lastAccess was unique, or EVICT key reason=tie when it was shared and the bytes rule chose the victim. An evicted entry is demoted to the soft tier under its key, keeping its lastAccess.

# Active draw and leaks

BEGIN_DRAW and END_DRAW keep a per key depth; the active set is every key with depth above zero. If RECYCLE runs while the depth for that key is above zero it is a leak: emit LEAK key, subtract its bytes from the strong total, remove it from the strong tier, and remove the key from the active set. After a leak a later END_DRAW on that key does nothing.

# Recycle dedup

When a RECYCLE succeeds (not drawing, stays in the strong tier), look for another strong entry with the same width, height, and config. If one exists, remove it, demote it to the soft tier, and emit DEDUP other_key; the recycled entry stays under its own key. At most one duplicate is removed per RECYCLE, the first one reached in strong tier iteration order.

# GC

GC empties the soft tier and emits GC cleared=n where n is how many entries were removed. The strong tier and active set are not affected.

# Silent noops

BEGIN_DRAW, END_DRAW, and RECYCLE on a key that is not in the strong tier emit nothing. They still advance currentTick.

# Output format

Each QUERY appends:

  pool maxBytes=32768 currentBytes=n
  strong:
    key=k w=w h=h config=C bytes=n lastAccess=t
    ...
  soft:
    key=k w=w h=h config=C bytes=n
    ...
  active:
    key=k depth=n
    ...
  events:
    event
    ...

currentBytes is strong tier bytes only. strong and soft rows are sorted by key ascending; strong rows carry lastAccess, soft rows do not. active lists only keys with depth above zero, sorted by key. events is the cumulative log in emission order: ALLOC key, EVICT key reason=lru or reason=tie, REUSE_STRONG key, REUSE_SOFT key, LEAK key, DEDUP key, GC cleared=n.

# What to do

Fix /app/src/com/example/bitmappool/BitmapPool.kt. Do not modify Main.kt or BitmapTypes.kt. The verifier compiles and runs your code.
