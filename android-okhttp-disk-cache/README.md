# codimango/android-okhttp-disk-cache

## Description

The agent fixes bugs in a Kotlin OkHttp/DiskLruCache-style HTTP response cache (`/app/src/com/example/httpcache/ResponseCache.kt`). The simulator processes STORE/OPEN/CLOSE/COMMIT/LOOKUP/TRIM/QUERY operations from a scenario file and prints a snapshot (memory hot set, disk journal, in-flight set, event log). Correct behavior spans: Vary-aware exact-match reuse (memory then disk then fresh store), byte-budgeted LRU eviction with demotion to disk, abort on commit of an in-flight in-memory entry, disk-tier promotion with cascade eviction, commit deduplication, TRIM clearing disk, and lastAccess preservation across reuse.

## Completion Rates

Each run is `k=5` trials. A trial scores `1.0` only if all 8 scenarios match expected output.

| Runner | Result |
| --- | --- |
| Oracle (reference `ResponseCache.kt`) | 3/3 — 1.000 deterministic |
| Opus 4.6 (`claude-opus-4-6`) | 5/5 |
| Avocado (`meta/avocado_dvsc_tester`) | 2/5 |
| Codex (`gpt-5.5`) | 0/5 |

(Rates observed on the v1.0 submission, before this revision documented the in-flight/eviction interaction. The task will be re-measured by the platform on submission.)

## Model Analysis

Behaviors the task exercises:

1. Vary-aware exact match — a cached response for the same url but a different vary value cannot satisfy a request; LOOKUP must search memory then disk then store fresh.
2. LRU eviction with disk demotion — when the memory byte total exceeds the 300000-byte budget, the entry with the smallest lastAccess (ties: smallest bytes, then key) is demoted to the disk journal under its own key, emitting EVICT reason=lru.
3. In-flight vs eviction — OPEN/CLOSE depth is bookkeeping only and does not protect an entry from eviction; an evicted in-flight entry moves to disk but keeps its in-flight depth, and a COMMIT on it (now off-memory) is a silent no-op.
4. Abort on in-flight commit — COMMIT of an in-memory entry whose in-flight depth > 0 aborts it (ABORT, bytes subtracted, removed from memory and in-flight set).
5. Disk promotion cascade — a disk exact match on LOOKUP promotes the entry back to memory, re-adding its bytes, which can itself trigger eviction within the same LOOKUP.
6. Commit dedup — a successful COMMIT demotes one other memory entry with the same (url, vary) to disk (DEDUP).
7. lastAccess preservation — REUSE_MEM/REUSE_DISK re-key the entry but preserve its original lastAccess (LOOKUP does not refresh it).

## Anti-Cheating

- Expected outputs live in `/tests` and are never copied into the agent image; the reference `ResponseCache.kt` is not agent-readable.
- No hint comments or answer-naming symbols in agent-visible source.
- Grading compiles and runs the agent's own `ResponseCache.kt` over 8 scenarios and compares full snapshots; solving in another language or hardcoding cannot pass.
