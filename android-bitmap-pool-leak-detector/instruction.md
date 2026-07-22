This is a bitmap pool like Glide or Coil, a feed allocates bitmaps recycles them and reuses them by width height and config. Right now it logs the wrong events in a few cases. Fix the BitmapPool file inside src so its query snapshots and event log match, leave the main and types files alone. The verifier builds and runs it.

The driver reads a scenario file one operation per line. ALLOC with key width height config allocates a fresh bitmap, its size in bytes is width times height times bytes per pixel and it counts toward memory budget right away and may trigger eviction. BEGIN_DRAW with key increments active draw depth for that key. END_DRAW decrements depth and at zero removes key from active set. RECYCLE with key returns bitmap to pool, if active depth is above zero it is a leak, emits LEAK and drops bitmap entirely and subtracts bytes and removes key from active set, otherwise it stays in strong tier and refreshes last access. ACQUIRE with new key width height config reuses a pool entry whose width height and config match exactly, or allocates fresh if none match, result is keyed under new key. TOUCH with list of keys sets last access of every listed strong entry to current tick so several entries can share one value, keys not in strong tier are ignored and TOUCH emits no event. GC clears whole soft tier and emits GC cleared count, strong tier and active set untouched. QUERY appends snapshot to output file.

Bytes per pixel is four for ARGB_8888 two for RGB_565 one for ALPHA_8, bitmap is width times height times bytes per pixel, max size is thirty two thousand seven hundred sixty eight, only strong tier counts toward cap.

Tick rises by one on every operation except QUERY. Strong entry tracks last access set on ALLOC, on fresh path of ACQUIRE, on successful RECYCLE, and on TOUCH. REUSE_STRONG and REUSE_SOFT keep existing last access and never refresh it, for soft reuse that is value entry held when demoted.

Tiers: Strong LRU ordered byte accounted against cap searched first by ACQUIRE. Soft flat list not byte accounted cleared only by GC.

ACQUIRE exact match means equal width height and config. Search strong first, on hit emit REUSE_STRONG new key, drop old key, restore under new key keeping its last access. If strong missed search soft, on hit emit REUSE_SOFT new key remove from soft promote to strong under new key keeping demoted last access, its bytes rejoin total and may trigger eviction. If neither matches allocate fresh emit ALLOC new key.

Eviction while strong total over cap remove one at a time until it fits. Victim smallest last access, if two share smallest fewest bytes first, if still tie smallest key first. Emit EVICT key reason lru when smallest unique or reason tie when shared and bytes or key rule chose victim. Evicted entry demoted to soft under its key keeping last access.

Active draw BEGIN_DRAW END_DRAW keep per key depth active set every key with depth above zero. RECYCLE leak case after leak later END_DRAW on that key does nothing.

Recycle dedup when RECYCLE succeeds not drawing look for another strong entry with same width height config, if exists remove it demote to soft emit DEDUP other key, recycled entry stays. At most one duplicate per RECYCLE first reached in strong iteration order.

GC empties soft and emits GC cleared count. Silent noops BEGIN_DRAW END_DRAW RECYCLE on key not in strong emit nothing but still advance tick.

Each QUERY appends pool maxBytes currentBytes, then strong rows sorted by key showing key width height config bytes last access, then soft rows sorted by key, then active rows sorted by key showing key depth, then events cumulative in emission order ALLOC EVICT REUSE_STRONG REUSE_SOFT LEAK DEDUP GC cleared.
