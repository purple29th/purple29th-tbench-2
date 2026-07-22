# codimango/android-okhttp-disk-cache

## Description

The agent fixes bugs in a Kotlin OkHttp DiskLruCache style HTTP response cache. The simulator processes STORE OPEN CLOSE COMMIT LOOKUP TOUCH TRIM QUERY operations from a scenario file and prints a snapshot with memory hot set, disk journal, in flight set, event log. Correct behavior spans Vary aware exact match reuse, byte budgeted LRU eviction with demotion to disk and three level tie break lastAccess bytes key, abort on commit of in flight in memory entry, disk tier promotion with cascade eviction and old lastAccess preservation, commit dedup, TRIM clearing disk, lastAccess preservation across reuse, and TOUCH creating shared ticks that force tie path.

We made it MRI hard like mri-volume-calc and depth-object-volume. In MRI, bright voxels are scattered and naive sum all bright over counts by 10 to 25 percent, only largest connected component passes 5 percent tolerance. Here, TOUCH scatters shared lastAccess ticks everywhere and LOOKUP preserves old small ticks from disk. Naive LRU that picks min by lastAccess only, or that refreshes on reuse to current tick, or that always assumes in flight entries are protected from eviction, evicts wrong key and fails. Disk promotion with old tick causes immediate re eviction, which only happens if you keep demoted lastAccess not current tick.

## Completion Rates

Each run is k=5 trials. A trial scores 1.0 only if all scenarios match expected output. At v1.4 4e659e2 it was 11 scenarios but 5/5 too easy, balance FAIL, Quality GOOD but reviewer disagreed on main in flight vs eviction under specified.

At v1.5 with 16 scenarios we added TOUCH operation to make tie possible (previously impossible without TOUCH, so bytes key tie break was dead code). New adversarial scenarios: tie_bytes_key same tick same bytes alphabetical, tie_bytes_three_keys three way tie, adversarial_touch_tie TOUCH shared ticks eviction by bytes, adversarial_soft_old_tick_chain STORE many evict to disk LOOKUP from disk old tick immediate re eviction, adversarial_gauntlet_full 7 QUERY stacking all 8 bugs including OPEN STORE eviction of in flight entry keeping depth, COMMIT on evicted in flight no op, DEDUP, TRIM, etc. Oracle 3/3 1.000 deterministic with 16 scenarios.

| Runner | Result at v1.4 4e659e2 | Expected at v1.5 |
| --- | --- | --- |
| Oracle | 3/3 1.000 | 3/3 1.000 |
| Opus | 5/5 | To be remeasured, should drop to 3-4/5 with gauntlet |
| Avocado | 5/5 too easy | Should drop to 0-2/5 with tie key and soft chain |
| Codex | 5/5 | Should drop |

Rates at f6d7c9b: bitmap-pool went from 5/5 too easy to 0/5 avocado PASS with similar hardening.

## Model Analysis

Behaviors the task exercises:

1. Vary aware exact match: same url different vary cannot satisfy.
2. LRU eviction with disk demotion and three level tie: smallest lastAccess, then smallest bytes, then key alphabetical. Emits EVICT reason lru. TOUCH creates shared ticks so tie path exercised.
3. In flight vs eviction: OPEN CLOSE depth bookkeeping does not protect from eviction, evicted in flight moves to disk but keeps depth while on disk and appears in inflight snapshot, COMMIT on now off memory in flight is silent no op not ABORT, not in memory rule takes precedence over abort.
4. Abort on in flight commit: COMMIT of in memory entry depth greater than zero aborts with ABORT, bytes subtracted, removed from memory and inflight.
5. Disk promotion cascade with old tick preservation: disk exact match on LOOKUP promotes back to memory re adding bytes which can trigger eviction inside same LOOKUP, and promoted entry keeps demoted lastAccess not currentTick, so it can be evicted immediately if its old tick small. Naive that refreshes fails.
6. Commit dedup: successful COMMIT demotes one other memory entry same url vary to disk DEDUP.
7. LastAccess preservation: REUSE_MEM and REUSE_DISK preserve original lastAccess, LOOKUP does not refresh.
8. TOUCH: sets lastAccess of every listed memory entry to current tick, several can share one value, ignored if not in memory, no event, but advances tick. Creates tie groups that force bytes key tie break.

## Anti-Cheating

- Expected outputs live in `/tests` and are never copied into the agent image; the reference `ResponseCache.kt` is not agent-readable.
- No hint comments or answer-naming symbols in agent-visible source.
- Grading compiles and runs the agent's own `ResponseCache.kt` over 8 scenarios and compares full snapshots; solving in another language or hardcoding cannot pass.
