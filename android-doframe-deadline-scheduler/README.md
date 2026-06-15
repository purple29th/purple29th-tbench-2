# codimango/android-doframe-deadline-scheduler

## Description

Kotlin simulator of Android Choreographer four-phase pipeline (INPUT then ANIMATION then INSETS then TRAVERSAL) plus the main-thread Looper / MessageQueue with sync barriers, async lanes, and frame-deadline-driven jank detection. Models real Android framework behavior across phase ordering, RESAMPLE_OFFSET cutoff, sync-barrier lifecycle, repeat-callback re-registration, REMOVE_FRAME during in-flight, vsync-rate transitions, async-through-barrier semantics, and jank-without-deferral.

## Completion Rates

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Anti-Cheating Analysis

- Per-behavior scenarios under /tests/expected/, mounted only at verifier time.
- Verifier compiles agent's source via kotlinc and runs each scenario.
- Reference solution implements all behaviors honestly.
