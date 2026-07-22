This is a bitmap pool like Glide or Coil. A feed allocates bitmaps, recycles them, and reuses them by width, height, and config. Right now it logs wrong events in a few cases. Fix the BitmapPool file inside src so its query snapshots and event log match. Leave the main and types files alone. The verifier builds and runs it.

The driver reads a scenario file one operation per line. ALLOC with key width height config creates a fresh bitmap. Its size is width times height times bytes per pixel. It counts toward memory budget right away and can trigger eviction. BEGIN_DRAW with key increments active draw depth. END_DRAW decrements depth and at zero removes key from active set. RECYCLE with key returns bitmap to pool. If active depth is above zero it is a leak. Emit LEAK and drop bitmap entirely, subtract bytes, remove key from active set. Otherwise it stays in strong tier and refreshes last access. ACQUIRE with new key width height config reuses a pool entry whose width, height, and config match exactly, or allocates fresh if none match. Result is keyed under new key. TOUCH with list of keys sets last access of every listed strong entry to current tick. Several entries can share one value that way. Keys not in strong tier are ignored. TOUCH emits no event. GC clears whole soft tier and emits GC cleared count. Strong tier and active set are untouched. QUERY appends snapshot to output file.

Bytes per pixel is four for ARGB_8888, two for RGB_565, one for ALPHA_8. Bitmap is width times height times bytes per pixel. Max size is thirty two thousand seven hundred sixty eight. Only strong tier counts toward cap.

Tick rises by one on every operation except QUERY. Strong entry tracks last access. It is set on ALLOC, on fresh path of ACQUIRE, on successful RECYCLE, and on TOUCH. REUSE_STRONG and REUSE_SOFT keep existing last access and never refresh it. For soft reuse that is the value the entry held when demoted.

Tiers. Strong is LRU ordered, byte accounted against cap, searched first by ACQUIRE. Soft is flat list, not byte accounted, cleared only by GC.

ACQUIRE exact match means equal width, height, and config. Search strong first. On hit emit REUSE_STRONG new key, drop old key, restore under new key keeping its last access. If strong missed, search soft. On hit emit REUSE_SOFT new key, remove from soft, promote to strong under new key keeping demoted last access. Its bytes rejoin total and may trigger eviction. If neither matches, allocate fresh and emit ALLOC new key.

Eviction. While strong total is over cap, remove one at a time until it fits. Victim is smallest last access. If two share smallest, fewest bytes first. If still tie, smallest key first. Emit EVICT key reason lru when smallest unique, or reason tie when shared and bytes or key rule chose victim. Evicted entry is demoted to soft under its key keeping last access.

Active draw. BEGIN_DRAW and END_DRAW keep per key depth. Active set is every key with depth above zero. After a leak, later END_DRAW on that key does nothing.

Recycle dedup. When RECYCLE succeeds without drawing, look for another strong entry with same width, height, and config. If exists, remove it, demote to soft, emit DEDUP other key. Recycled entry stays. At most one duplicate per RECYCLE, first reached in strong iteration order.

GC empties soft and emits GC cleared count. Silent noops. BEGIN_DRAW, END_DRAW, and RECYCLE on key not in strong emit nothing, but still advance tick.

Each QUERY appends pool maxBytes currentBytes, then strong rows sorted by key showing key width height config bytes last access, then soft rows sorted by key, then active rows sorted by key showing key depth, then events cumulative in emission order ALLOC EVICT REUSE_STRONG REUSE_SOFT LEAK DEDUP GC cleared.
