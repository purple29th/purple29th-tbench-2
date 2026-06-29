# codimango/android-doframe-deadline-scheduler

## Description

Kotlin simulator of Android Choreographer four-phase pipeline (INPUT then ANIMATION then INSETS then TRAVERSAL) plus the main-thread Looper / MessageQueue with sync barriers, async lanes, vsync-rate transitions, and frame-deadline-driven jank detection. The agent fixes DoFrameScheduler.kt so the simulator's frame log, queue snapshot, and event stream match the expected output across 12 scenarios.

## Completion Rates

Each run is k=5 trials. A trial scores 1.0 only if every scenario's output matches its expected file exactly.

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | 2/5 (platform validation, genuine split) |
| Opus 4.6 (claude-opus-4-6)         | 0/5 (infra-suspect null-exception; re-calibrating at HEAD) |

## Model Analysis

Failure modes the task surfaces, drawn from real Android framework behavior:

1. Missing INSETS phase. The pipeline is four phases (INPUT, ANIMATION, INSETS, TRAVERSAL); implementations that drop INSETS route insets-phase callbacks to the wrong slot or never run them.
2. Resample boundary off-by-one. The cutoff is eventTime <= vsyncTime - 4; implementations using strict < defer an event that should dispatch this frame.
3. Sync-barrier lift placement. The barrier is lifted at the start of TRAVERSAL, not at frame start, so a sync message posted before SCHEDULE_TRAVERSALS still defers through the INPUT/ANIMATION/INSETS drains.
4. Vsync-rate transition timing. SET_VSYNC_RATE takes effect one frame later (the pending rate is applied at the end of the next DO_FRAME); the current in-flight frame keeps its already-computed interval and deadline. Implementations that apply the new rate immediately compute the current frame's deadline with the wrong interval.
5. Idempotent SCHEDULE_TRAVERSALS. A second call while a barrier is already active is a no-op and emits no second MSG_BARRIER.
6. Unconditional MSG_BARRIER_LIFTED. Every frame emits MSG_BARRIER_LIFTED at TRAVERSAL start regardless of whether a barrier was active; implementations that guard the emission on barrier state under-report it.
7. Jank without deferral. When work overruns the deadline, the frame is marked jank and a JANK event emits, but remaining work still executes in the same frame rather than deferring to the next.
8. removeFrame purges all matching tokens, not just the first.

## Anti-Cheating Analysis

- 12 per-behavior scenarios under /tests/expected/, mounted only at verifier time. Each scenario isolates one behavior; jank, vsync transitions, DRAIN_QUEUE budget semantics, and async-through-barrier are each exercised independently.
- Verifier compiles the agent's source via kotlinc and runs each scenario; reward is all-or-nothing per scenario.
- Reference solution implements every behavior honestly and is never agent-readable.

