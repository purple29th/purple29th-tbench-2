# Setting

Simulates an OkHttp/DiskLruCache-style HTTP response cache: responses are stored under a byte budget, recently-used responses stay in an in-memory hot set, evicted responses spill to a disk journal, and an in-flight reader is tracked only by a depth counter (this bookkeeping does NOT exempt the entry from eviction). Bugs in this layer either over-fill the cache (exceeding the disk budget) or serve the wrong cached response for a request whose Vary headers differ.

The current implementation in /app/src/com/example/httpcache/ResponseCache.kt produces wrong output across several scenarios. Fix it.

# Operations (/app/scenario.txt)

- STORE <key> <url> <vary> <bytes> — store a fresh response. It counts toward the budget immediately and may itself trigger eviction.
- OPEN <key> — increment the in-flight reader depth for <key>.
- CLOSE <key> — decrement the in-flight reader depth for <key> (remove from the in-flight set when it reaches 0).
- COMMIT <key> — finish writing the entry. It has effect only if <key> is currently in memory; if <key> is not in memory it is a silent no-op, even when the key is still in-flight (see Silent no-ops). If <key> is in memory and its in-flight depth is greater than zero, abort it entirely (see abort handling); otherwise the entry stays in memory and its lastAccess is updated.
- LOOKUP <key> <url> <vary> <bytes> — serve a cached response whose (url, vary) match exactly, or store fresh if none match. Search order: memory, then disk, then fresh store. The served entry is keyed under the new <key>.
- TRIM — clear the disk journal entirely. The memory hot set and the in-flight set are untouched.
- QUERY — append a snapshot to /app/output.txt.

# Byte accounting

A response's bytes are given directly. The disk budget is 300000 bytes. Only the memory hot set counts toward the budget.

# Tick / lastAccess

A monotonic currentTick increments by 1 on every input op except QUERY. Each memory entry tracks lastAccess — the tick at which it was most recently stored, served (under its current key), or committed into memory.

# Tiers and reuse

The cache has two tiers:

- Memory hot set. LRU-ordered, byte-accounted toward the budget. The lookup target for LOOKUP.
- Disk journal. A flat list. Not byte-accounted. Cleared only by TRIM.

LOOKUP:

- Memory exact match: emit REUSE_MEM <new_key>. The matched entry's old key is removed; the entry is re-stored under <new_key> with its lastAccess preserved from the matched entry (LOOKUP does not refresh lastAccess).
- Disk exact match (only checked if memory missed): emit REUSE_DISK <new_key>. The entry is removed from disk and promoted to memory under <new_key> with its lastAccess preserved from the disk entry. Its bytes are re-added to the memory total, which may itself trigger eviction inside the same LOOKUP.
- No match: store fresh. Emit STORE <new_key>. The new bytes are added to the memory total, which may trigger eviction.

Exact match means both url and vary are equal. A cached response for the same url but a different vary value cannot satisfy the request.

# Eviction

Eviction is memory-only and runs whenever the memory byte total exceeds the budget. The cache repeatedly removes one entry until the total fits at or below the budget. The victim is the entry with the smallest lastAccess; ties are broken by the smallest bytes, then by key ascending. An entry whose in-flight depth is greater than zero is NOT exempt from eviction — it is chosen and demoted to disk like any other entry, and it keeps its in-flight depth while it sits on disk (so it still appears in the inflight snapshot). Each evicted entry emits an EVICT <key> reason=lru event and is demoted to the disk journal under its existing key. It is not destroyed.

# Abort handling

OPEN <key> and CLOSE <key> maintain a per-key in-flight depth. The in-flight set lists keys whose depth is greater than zero.

If COMMIT <key> is called while <key> is in memory and its in-flight depth is greater than zero:

- Emit ABORT <key>.
- Subtract the entry's bytes from the memory total.
- Remove the entry from memory.
- Remove the key from the in-flight set.

After an abort, subsequent CLOSE <key> calls are silent no-ops (the key is no longer tracked).

If an in-flight entry was evicted to disk while a reader was still open, it is no longer in memory. A later COMMIT <key> on it therefore matches the not-in-memory rule and is a silent no-op: no ABORT is emitted, and the key stays in the in-flight set until CLOSE brings its depth back to zero. The not-in-memory rule takes precedence over the abort rule.

# Commit deduplication

When COMMIT <key> succeeds (the entry was not in-flight and stays in memory), the cache then checks whether any other memory entry has the same (url, vary) as the committed entry. If one exists, that other entry is removed from memory, demoted to disk, and a DEDUP <other_key> event is emitted. The committed entry itself stays in memory under its own key. Only one duplicate is removed per COMMIT.

# Silent no-ops

OPEN, CLOSE, and COMMIT on a key not currently in memory produce no event. They still advance currentTick.

# Output format

Each QUERY appends a snapshot:

    cache budget=300000 currentBytes=<n>
    memory:
      key=<k> url=<u> vary=<v> bytes=<n> lastAccess=<tick>
      ...
    disk:
      key=<k> url=<u> vary=<v> bytes=<n>
      ...
    inflight:
      key=<k> depth=<n>
      ...
    events:
      <event>
      ...

- currentBytes is the sum of memory-hot-set bytes only.
- memory rows sorted by key ascending; each row carries lastAccess.
- disk rows sorted by key ascending; no lastAccess.
- inflight rows sorted by key ascending; only keys with depth > 0.
- events is the cumulative log in emission order: STORE <key>, EVICT <key> reason=lru, REUSE_MEM <key>, REUSE_DISK <key>, ABORT <key>, DEDUP <key>, TRIM cleared=<n>.

# What you need to do

Fix /app/src/com/example/httpcache/ResponseCache.kt. Do not modify Main.kt or CacheTypes.kt. The verifier compiles and runs your fixed code automatically.

# Reference build (local debugging only)

    cd /app
    kotlinc src/com/example/httpcache/*.kt -include-runtime -d /app/sim.jar
    java -jar /app/sim.jar scenario.txt output.txt
