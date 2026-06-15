# codimango/android-bitmap-pool-leak-detector

## Description

A Kotlin simulator of an Android BitmapPool modeled on Glide/Coil/Fresco. Strong-tier LRU + soft-tier fallback + active-draw tracking + GC. The current BitmapPool.kt has six interlocking bugs across reuse exact-match, eviction tie-break, leak-on-active-draw, soft-tier promotion, eviction-on-fresh-alloc, and active-draw cleanup. The agent fixes BitmapPool.kt so the simulator's snapshot + event log matches expectations across six per-trap scenarios plus one integration scenario.

## Completion Rates

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

1. Config equality on reuse — ARGB_8888 cannot satisfy RGB_565 at matching dimensions.
2. LRU tie-break by bytes — when two entries share the same lastAccess, evict the smaller one first.
3. Recycle-during-active-draw is a leak — emit LEAK, drop bitmap, drop active-draw state.
4. Soft promotion cascades — promotion may itself push the strong tier over the cap and trigger eviction.
5. ALLOC and the fresh-allocate path of ACQUIRE count immediately and can themselves trigger eviction.
6. GC clears soft tier only; strong tier and active-draw set are preserved.

## Anti-Cheating Analysis

- Multiple per-behavior scenarios — six focused + one integration. Each isolates a trap class with its own expected.txt.
- Test files protected — expected outputs live under /tests/expected/, not in the agent's /app/ view.
- Verifier compiles agent's source — kotlinc builds the jar and runs each scenario.
- Reference solution genuine — solution/BitmapPool.kt implements all six behaviors honestly.
