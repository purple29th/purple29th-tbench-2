# codimango/android-media-segment-cache

## Description

A Kotlin simulator of an ExoPlayer-style media segment buffer cache: a bounded in-memory buffer + a disk cache, with playing-segment pinning and a TRIM (onTrimMemory) op. The current SegmentCache.kt has interlocking bugs across exact-match reuse, LRU tie-break, stall-on-play, disk-tier promotion, buffer-on-fresh eviction, release dedup, and lastAccess preservation. The agent fixes SegmentCache.kt so the snapshot + event log matches expectations across eight scenarios.

## Completion Rates

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | 4/5 (0.80) |
| Opus 4.6 (claude-opus-4-6)         | 5/5 (1.00) |

## Model Analysis

1. Exact-match reuse on (track, durMs, bitrate) — same track+duration at a different bitrate cannot satisfy the request.
2. RELEASE during playback is a STALL — emit STALL, drop the segment, drop the playing state.
3. Disk-tier promotion cascades — promotion re-adds bytes and may trigger eviction inside the same REQUEST.
4. BUFFER and the fresh path of REQUEST count immediately and can self-evict.
5. TRIM clears the disk cache only; memory and playing set are preserved.
6. RELEASE deduplicates a same-spec memory entry to disk.
7. REUSE_MEM and REUSE_DISK preserve the matched entry's lastAccess rather than refreshing it.

## Anti-Cheating Analysis

- Eight scenarios under /tests/expected/, mounted only at verifier time.
- Verifier compiles the agent's source via kotlinc and runs each scenario; reward is all-or-nothing per scenario.
- Reference solution implements every behavior honestly and is never agent-readable.

<!-- revalidate ebd30f8 -->

<!-- revalidate -->
