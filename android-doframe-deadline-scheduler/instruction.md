# Setting

A Kotlin simulator of the Android Choreographer.doFrame() loop and the main-thread Looper/MessageQueue pipeline that drives every Android UI frame. Each DO_FRAME represents one vsync; the simulator runs Choreographer's four-phase callback pipeline (INPUT then ANIMATION then INSETS then TRAVERSAL), drains the Looper message queue between phases, and emits a jank event when work overruns the frame deadline. This is the production code path that produces dropped frames and ANRs in real apps.

# Operations

Operations are read from /app/scenario.txt.

- SET_VSYNC_RATE <hz> — set vsync rate (60, 90, 120). Interval = 1000 / hz ms (integer division). The new rate is applied at the end of the next DO_FRAME, so it first takes effect one frame later; the next frame keeps the previous interval.
- POST_FRAME <token> <phase> <costMs> <repeat> — register a frame callback for the next frame. phase in {INPUT, ANIMATION, INSETS, TRAVERSAL}. repeat in {once, repeat}.
- REMOVE_FRAME <token> — cancel a frame callback (queued-for-next-frame and in-flight).
- POST_INPUT <eventTime> <x> <y> — queue an input event at logical time eventTime.
- POST_MESSAGE <priority> <costMs> — queue a Looper message. priority in {sync, async}.
- SCHEDULE_TRAVERSALS — post a sync barrier that blocks sync messages until the next frame's TRAVERSAL begins.
- DO_FRAME <vsyncTime> — run one frame: resample input, execute 4 phases, drain queue per rules, detect jank.
- DRAIN_QUEUE <budgetMs> — drain message queue outside a frame, up to budgetMs (no partial dispatch).
- QUERY — append a snapshot to /app/output.txt.

# Frame intervals, deadline, and time

| Hz | frameIntervalMs |
|---|---|
| 60 | 16 |
| 90 | 11 |
| 120 | 8 |

Default rate at start: 60 Hz (frameIntervalMs = 16). For frame n with DO_FRAME <vsyncTime>, deadline = vsyncTime + frameIntervalMs.

currentTime advances only by dispatched message costMs and executed frame callback costMs. Phase transitions, queue checks, barrier lift, and rate changes advance time by 0. At the start of each DO_FRAME, if currentTime < vsyncTime, currentTime jumps forward to vsyncTime.

Frame counter starts at 1 on the first DO_FRAME and increments once per DO_FRAME.

# Choreographer pipeline (DO_FRAME)

For DO_FRAME <vsyncTime>, define deadline = vsyncTime + frameIntervalMs.

1. Input resampling. Dispatch this frame: events with eventTime <= vsyncTime - 4. Defer: events with eventTime > vsyncTime - 4. If any dispatched: emit INPUT_BATCH count=<n> oldestEventTime=<tOldest>. If any deferred: emit INPUT_DEFERRED count=<n>. Dispatch/defer does not advance currentTime.
2. INPUT phase callbacks. Execute all registered INPUT callbacks (posting order). For each: emit FRAME_CALLBACK <token>, advance currentTime += costMs.
3. Drain async messages (between INPUT and ANIMATION). While currentTime < deadline, dispatch queued async messages FIFO. Emit MSG_DISPATCH priority=async costMs=<n> per dispatch. Advance currentTime += costMs. Stop when currentTime >= deadline or no eligible async remains.
4. ANIMATION phase callbacks. Same mechanics as INPUT for ANIMATION callbacks.
5. Drain async messages (between ANIMATION and INSETS). Same as step 3.
6. INSETS phase callbacks. Same mechanics as INPUT for INSETS callbacks.
7. Drain async messages (between INSETS and TRAVERSAL). Same as step 3.
8. TRAVERSAL phase callbacks + barrier lift. At the start of TRAVERSAL, the simulator emits MSG_BARRIER_LIFTED and marks the barrier inactive. The event is emitted on every frame, regardless of whether a barrier was previously active. Execute TRAVERSAL callbacks (posting order), emitting FRAME_CALLBACK <token> and advancing time by their costMs.
9. Final drain (after TRAVERSAL). While currentTime < deadline, dispatch eligible messages: async FIFO always eligible; sync FIFO eligible only if barrier inactive. Emit MSG_DISPATCH priority=<sync|async> costMs=<n> per dispatch.
10. Jank check. If currentTime > deadline at any point during the frame: mark the frame jank=true, emit JANK frame=<n> overrunMs=<currentTime - deadline> once, at end of frame. Work is not deferred due to jank.

# Frame callbacks

POST_FRAME registers for the next frame, not the currently executing frame. Within a phase, callbacks execute in posting order. Re-posted repeat callbacks join the next frame at the end of that phase's queue.

repeat semantics: once = removed after it executes; repeat = re-registers for the next frame after executing, does not run again in the current frame.

REMOVE_FRAME <token> removes the token from queued-for-next-frame and in-flight callbacks. If called during a frame, also scrubs any next-frame re-registration that a repeat callback would have produced.

# Input resampling

Constant: RESAMPLE_OFFSET = 4 ms. Cutoff: dispatch this frame iff eventTime <= vsyncTime - 4.

Coalesce all dispatched events per frame into one event: INPUT_BATCH count=<n> oldestEventTime=<tMin>. Deferred events per frame emit one event: INPUT_DEFERRED count=<n>. (x, y) payloads are not printed in snapshots.

# MessageQueue and barriers

Two FIFO lanes: sync, async. When barrier active: sync messages do not dispatch, async messages dispatch normally. When barrier inactive: both lanes may dispatch.

SCHEDULE_TRAVERSALS posts a sync barrier and emits MSG_BARRIER. If a sync barrier is already active when SCHEDULE_TRAVERSALS is called, the call is a no-op: no second MSG_BARRIER event is emitted. Every DO_FRAME emits MSG_BARRIER_LIFTED at the start of its TRAVERSAL phase regardless of prior barrier state.

DRAIN_QUEUE <budgetMs> (outside frames) drains messages for up to budgetMs total dispatch cost. A message that would exceed remaining budget is not dispatched (no partial dispatch). Per step: dispatch eligible async first, then dispatch eligible sync if barrier inactive. Stop when no message fits remaining budget, both lanes empty, or barrier blocks all remaining messages.

# Vsync rate transitions

SET_VSYNC_RATE <hz> records a pending interval that is applied at the end of the next DO_FRAME, so that frame still uses the current interval and deadline and the new interval first takes effect on the following frame. A frame in progress keeps its already-determined interval/deadline. Emit VSYNC_RATE_CHANGED from=<oldHz> to=<newHz> when processed (time cost 0).

# Output format (QUERY)

Each QUERY appends:

    vsync rate=<hz> frameIntervalMs=<n> currentTime=<t>
    frames:
      frame=<n> vsyncTime=<t> deadlineMs=<t+interval> spentMs=<x> jank=<true|false>
        INPUT: <token>, <token>, ...
        ANIMATION: <token>, ...
        INSETS: <token>, ...
        TRAVERSAL: <token>, ...
      ...
    queue:
      sync=<n> async=<n> barrier=<active|inactive>
    next-frame callbacks:
      <token>, <token>, ...
    events:
      <event>
      ...

frames: cumulative list in order. Each phase line always present; empty phase prints as PHASE: with no tokens. Phase rosters list tokens that executed in that phase, in dispatch order.

queue: current pending message counts and barrier state at query time.

next-frame callbacks: current tokens registered for the next DO_FRAME, combined across phases, in registration order.

events: cumulative log in emission order. Event types: FRAME_CALLBACK <token>, INPUT_BATCH count=<n> oldestEventTime=<t>, INPUT_DEFERRED count=<n>, MSG_DISPATCH priority=<sync|async> costMs=<n>, MSG_BARRIER, MSG_BARRIER_LIFTED, JANK frame=<n> overrunMs=<x>, VSYNC_RATE_CHANGED from=<hz> to=<hz>.

# What you need to do

Fix /app/src/com/example/choreographer/DoFrameScheduler.kt. Do not modify Main.kt or FrameTypes.kt. The verifier compiles and runs automatically.

# Reference build (local debugging only)

From /app:

    kotlinc src/com/example/choreographer/*.kt -include-runtime -d app.jar
    java -jar app.jar scenario.txt output.txt
