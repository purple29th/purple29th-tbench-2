# codimango/android-okhttp-disk-cache

## Description

A Kotlin simulator of an OkHttp/DiskLruCache-style HTTP response cache: a byte-budgeted in-memory hot set + a disk journal, with in-flight-reader pinning and a TRIM op. The current ResponseCache.kt has interlocking bugs across Vary-aware exact-match reuse, LRU eviction, abort-on-inflight, disk-tier promotion, store-on-fresh eviction, commit dedup, and lastAccess preservation. The agent fixes ResponseCache.kt so the snapshot + event log matches expectations across eight scenarios.

## Completion Rates

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

1. Vary-aware exact match — a response for the same url but a different vary value cannot satisfy the request. Matching on url alone serves the wrong cached entry.
2. RELEASE/COMMIT during an in-flight read is an ABORT — emit ABORT, drop the entry, drop the in-flight state.
3. Disk-tier promotion cascades — promotion re-adds bytes and may trigger eviction inside the same LOOKUP.
4. STORE and the fresh path of LOOKUP count immediately and can self-evict.
5. TRIM clears the disk journal only; memory and in-flight set are preserved.
6. COMMIT deduplicates a same-(url,vary) memory entry to disk.
7. REUSE_MEM and REUSE_DISK preserve the matched entry's lastAccess rather than refreshing it.

## Anti-Cheating Analysis

- Eight per-behavior scenarios under /tests/expected/, mounted only at verifier time.
- Verifier compiles the agent's source via kotlinc and runs each scenario; reward is all-or-nothing per scenario.
- Reference solution implements every behavior honestly and is never agent-readable.
