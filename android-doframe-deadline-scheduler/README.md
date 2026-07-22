# codimango/android-doframe-deadline-scheduler

## Description

Kotlin simulator of Android Choreographer four-phase pipeline (INPUT then ANIMATION then INSETS then TRAVERSAL) plus the main-thread Looper / MessageQueue with sync barriers, async lanes, vsync-rate transitions, and frame-deadline-driven jank detection. The agent fixes DoFrameScheduler.kt so the simulator's frame log, queue snapshot, and event stream match the expected output across 15 scenarios.

## Completion Rates

Each run is k=5 trials. A trial scores 1.0 only if every scenario's output matches its expected file exactly. 15 scenarios including dedicated jank, vsync, drain_queue, double_token_purge, and async cases.

| Model                              | Pass rate (k=5/6)                  |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | 0/6 (genuine) – vsync emission ordering ambiguity was dominant failure |
| Opus 4.8 (claude-opus-4-8)         | 4/5 (genuine) after fix            |
| GPT-5.5                            | 1/5                                |

Note: After vsync spec clarification, Opus failure rate drops; vsync cases were the cluster with byte-identical wrong emission position before fix.

## Model Analysis

Failure modes the task surfaces, drawn from real Android framework behavior:

1. Missing INSETS phase. The pipeline is four phases (INPUT, ANIMATION, INSETS, TRAVERSAL); implementations that drop INSETS route insets-phase callbacks to the wrong slot or never run them.
2. Resample boundary off-by-one. The cutoff is eventTime <= vsyncTime - 4; implementations using strict < defer an event that should dispatch this frame.
3. Sync-barrier lift placement. The barrier is lifted at the start of TRAVERSAL, not at frame start, so a sync message posted before SCHEDULE_TRAVERSALS still defers through the INPUT/ANIMATION/INSETS drains.
4. Vsync-rate transition timing. SET_VSYNC_RATE emits VSYNC_RATE_CHANGED immediately at command-read time (when the SET line is processed), but its new interval is applied only at end of next DO_FRAME; the current in-flight frame and the next frame keep their old interval/deadline. Implementations that emit at apply time or apply immediately compute wrong deadline or wrong event ordering. Example: DO_FRAME 0, SET_VSYNC_RATE 120, DO_FRAME 16, DO_FRAME 24 => events MSG_BARRIER_LIFTED (f1), VSYNC_RATE_CHANGED (immediate), MSG_BARRIER_LIFTED (f2 deadline still 32), MSG_BARRIER_LIFTED (f3 deadline 32 with new interval).
5. Idempotent SCHEDULE_TRAVERSALS. A second call while a barrier is already active is a no-op and emits no second MSG_BARRIER.
6. Unconditional MSG_BARRIER_LIFTED. Every frame emits MSG_BARRIER_LIFTED at TRAVERSAL start regardless of whether a barrier was active; implementations that guard the emission on barrier state under-report it.
7. Jank without deferral. When work overruns the deadline, the frame is marked jank and a JANK event emits, but remaining work still executes in the same frame rather than deferring to the next.
8. removeFrame purges all matching tokens, not just the first – enforced by double_token_purge scenario.

## Anti-Cheating Analysis

- 15 per-behavior scenarios under /tests/expected/. Each scenario isolates one behavior; jank, vsync transitions, DRAIN_QUEUE budget semantics, async-through-barrier, and double token purge are each exercised independently.
- Hardened verifier: at grade time the verifier bundles /tests into a base64 tar stored only in shell memory (not exported), then rm -rf /tests so no expected file exists on filesystem during agent execution. Scenario inputs are re-materialized under randomized UUID filenames (e.g. /app/scenarios/<uuid>.txt) with UUID->name mapping kept only in shell memory, so the agent's /proc/self/cmdline contains only a UUID, not the scenario stem, and cannot derive the corresponding expected filename. After the agent jar run, /tests is restored from the in-memory bundle and UUID outputs are translated back to named outputs for pytest comparison. Prior bypass that read /tests/expected/ or /tmp/tests.hidden and echoed it verbatim now scores 0 because expected files do not exist during jar execution.
- Verifier compiles the agent's source via kotlinc and runs each scenario; reward is all-or-nothing per scenario (binary).
- Reference solution is never agent-readable during agent execution; it exists only in /solution/ which is not mounted at grade time.


<!-- revalidate doframe 81c0f12 -->
