# Setting

Simulates an ExoPlayer-style media segment buffer cache: a player buffers media segments ahead of playback, keeps recently-used segments in a bounded in-memory buffer, and spills evicted segments to a disk cache. Bugs in this layer either over-fill memory (OOM) or stall playback by dropping a segment that is currently being played.

The current implementation in /app/src/com/example/mediacache/SegmentCache.kt produces wrong output across several scenarios. Fix it.

# Operations (/app/scenario.txt)

- BUFFER <key> <track> <durMs> <bitrate> — buffer a fresh segment. Its byte size is durMs * bitrate / 8 (integer division). The segment counts toward the memory budget immediately and may itself trigger eviction.
- PLAY <key> — increment the playing depth counter for <key>.
- STOP <key> — decrement the playing depth counter for <key> (remove from the playing set when it reaches 0).
- RELEASE <key> — return the segment to the cache. If the playing depth is greater than zero, drop the segment entirely (see stall detection); otherwise the entry stays in memory and its lastAccess is updated.
- REQUEST <key> <track> <durMs> <bitrate> — reuse a cached segment whose (track, durMs, bitrate) match exactly, or buffer fresh if none match. Search order: memory, then disk, then fresh buffer. The reused segment is keyed under the new <key>.
- TRIM — clear the disk cache entirely. The memory buffer and the playing set are untouched.
- QUERY — append a snapshot to /app/output.txt.

# Byte accounting

A segment's bytes are durMs * bitrate / 8 (integer division). The memory budget is 300000 bytes. Only the memory buffer counts toward the budget.

# Tick / lastAccess

A monotonic currentTick increments by 1 on every input op except QUERY. Each memory entry tracks lastAccess — the tick at which it was most recently buffered, requested (under its current key), or released into memory.

# Tiers and reuse

The cache has two tiers:

- Memory buffer. LRU-ordered, byte-accounted toward the budget. The lookup target for REQUEST.
- Disk cache. A flat list. Not byte-accounted. Cleared only by TRIM.

REQUEST:

- Memory exact match: emit REUSE_MEM <new_key>. The matched entry's old key is removed; the entry is re-stored under <new_key> with its lastAccess preserved from the matched entry (REQUEST does not refresh lastAccess).
- Disk exact match (only checked if memory missed): emit REUSE_DISK <new_key>. The entry is removed from disk and promoted to memory under <new_key> with its lastAccess preserved from the disk entry. Its bytes are re-added to the memory total, which may itself trigger eviction inside the same REQUEST.
- No match: buffer fresh. Emit BUFFER <new_key>. The new bytes are added to the memory total, which may trigger eviction.

Exact match means all three of track, durMs, and bitrate are equal. A cached segment for the same track and duration but a different bitrate cannot satisfy the request.

# Eviction

Eviction is memory-only and runs whenever the memory byte total exceeds the budget. The cache repeatedly removes one entry until the total fits at or below the budget.

The victim is chosen as follows:

- Smallest lastAccess wins.
- If two entries share the smallest lastAccess, the one with smaller bytes is evicted first.

Each evicted entry emits an EVICT <key> reason=lru event. Evicted entries are demoted to the disk cache under their existing key. They are not destroyed.

# Stall detection

PLAY <key> and STOP <key> maintain a per-key playing depth. The playing set lists keys whose depth is greater than zero.

If RELEASE <key> is called while the playing depth for <key> is greater than zero:

- Emit STALL <key>.
- Subtract the segment's bytes from the memory total.
- Remove the segment from memory.
- Remove the key from the playing set.

After a stall, subsequent STOP <key> calls are silent no-ops (the key is no longer tracked).

# Release deduplication

When RELEASE <key> succeeds (the segment was not playing and stays in memory), the cache then checks whether any other memory entry has the same (track, durMs, bitrate) as the released segment. If one exists, that other entry is removed from memory, demoted to disk, and a DEDUP <other_key> event is emitted. The released segment itself stays in memory under its own key. Only one duplicate is removed per RELEASE.

# Silent no-ops

PLAY, STOP, and RELEASE on a key not currently in memory produce no event. They still advance currentTick.

# Output format

Each QUERY appends a snapshot:

    cache budget=300000 currentBytes=<n>
    memory:
      key=<k> track=<t> dur=<d> bitrate=<b> bytes=<n> lastAccess=<tick>
      ...
    disk:
      key=<k> track=<t> dur=<d> bitrate=<b> bytes=<n>
      ...
    playing:
      key=<k> depth=<n>
      ...
    events:
      <event>
      ...

- currentBytes is the sum of memory-buffer bytes only.
- memory rows sorted by key ascending; each row carries lastAccess.
- disk rows sorted by key ascending; no lastAccess.
- playing rows sorted by key ascending; only keys with depth > 0.
- events is the cumulative log in emission order: BUFFER <key>, EVICT <key> reason=lru, REUSE_MEM <key>, REUSE_DISK <key>, STALL <key>, DEDUP <key>, TRIM cleared=<n>.

# What you need to do

Fix /app/src/com/example/mediacache/SegmentCache.kt. Do not modify Main.kt or MediaTypes.kt. The verifier compiles and runs your fixed code automatically.

# Reference build (local debugging only)

    cd /app
    kotlinc src/com/example/mediacache/*.kt -include-runtime -d /app/sim.jar
    java -jar /app/sim.jar scenario.txt output.txt
