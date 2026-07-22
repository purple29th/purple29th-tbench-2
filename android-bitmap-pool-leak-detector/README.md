# codimango/android-bitmap-pool-leak-detector

A Kotlin simulator of an Android BitmapPool modeled on Glide or Coil. Strong tier LRU plus soft tier fallback plus active draw tracking plus GC. The reference has eight interlocking bugs across reuse exact match, eviction tie break by bytes and key, leak on active draw, soft tier promotion keeping old lastAccess, dedup on recycle, and active draw cleanup.

We made it MRI hard. Like MRI where bright voxels are scattered and naive sum all bright over counts by 10 to 25 percent, here TOUCH scatters shared lastAccess ticks everywhere. Naive LRU that picks min by lastAccess only, or that refreshes on REUSE to current tick, evicts wrong key and emits wrong reason tie versus lru. An agent that always emits reason lru and never implements bytes and key tie break can pass old 8 scenarios with distinct ticks but fails the new tie scenarios where two or three entries share same tick and same bytes.

Enforced behaviors:
1. Config equality on reuse: ARGB_8888 cannot satisfy RGB_565 at same dimensions.
2. LRU tie break by bytes then key: when entries share smallest lastAccess, smaller bytes first, if bytes equal smallest key first, reason is tie when shared tick caused choice.
3. TOUCH creates shared ticks: several entries can have identical lastAccess, triggering tie path.
4. REUSE keeps old lastAccess: REUSE_STRONG keeps its old lastAccess, REUSE_SOFT keeps demoted lastAccess not current tick. If you refresh, soft promotion with small old tick that should be evicted immediately stays and later evictions go wrong.
5. Soft promotion cascades: promotion may itself push strong over cap and trigger eviction chain.
6. Recycle during active draw is leak: emit LEAK, drop bitmap and active state, later END_DRAW no op.
7. Recycle dedup: successful RECYCLE looks for another strong entry same spec, demotes it to soft, emits DEDUP.
8. GC clears soft only.

## Completion Rates at v1.3 4e659e2

| Model | Pass rate |
|-------|-----------|
| Oracle | 3/3 1.00 deterministic, now 17 scenarios |
| Avocado | 5/5 1.00 too easy before hardening, platform SEV causing cancels locally, expected to drop to 2/5 with new tie key and soft old tick traps |
| Opus | 5/5 1.00 |
| gpt-5.5 | 1/5 0.20 |

Quality at 4e659e2: 6 good 1 warn, Struct PASS, Oracle PASS, Balance FAIL too easy. Justin review noted tie reason never triggered and REUSE_SOFT contradiction. v1.4 adds 5 adversarial scenarios plus docs fix: evict_tie already exists, plus tie_bytes_key same bytes alphabetical, tie_bytes_three_keys three way tie, adversarial_soft_old_tick_chain old tick immediate eviction, adversarial_dedup_leak_touch leak plus dedup plus touch tie, adversarial_gauntlet_full 7 QUERY stacking all 8 bugs. Oracle 1.000 verified. Spec now mentions bytes then key and reason tie versus lru.

## Model Analysis

Natural but wrong is to implement pure LRU min lastAccess and refresh on reuse to current tick, and always emit reason lru. That passes simple evictions but fails tie scenarios where TOUCH made ticks equal and bytes and key decide, and fails soft chain where preserved old tick 1 should be evicted immediately after promotion. Like MRI largest connected component versus sum all bright, here you need 3 level sort lastAccess bytes key and never refresh on reuse.

## Anti-Cheating Analysis

- 17 scenarios now, 12 old plus 5 new adversarial. Each isolates trap class with its own expected.
- Expected outputs live under tests expected, not in app view. Verifier hides tests and app scenarios during jar execution and copies scenarios back, so agent cannot read expected via file read.
- Verifier compiles agent source kotlinc builds jar and runs each scenario, fails closed on build error with reward 0 and clears stale outputs.
- Salted digests not needed because Kotlin output is textual snapshot, hiding is primary defense.
- Reference solution genuine implements all 8 behaviors honestly, iterative sort by lastAccess bytes key.
