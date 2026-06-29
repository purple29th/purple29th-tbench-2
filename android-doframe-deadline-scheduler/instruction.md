This is a simulator of the Android Choreographer.doFrame() loop and the main-thread Looper/MessageQueue that drive each UI frame. Each DO_FRAME is one vsync: it runs the four phases INPUT, ANIMATION, INSETS, TRAVERSAL in that order, drains the Looper queue between phases, and flags jank when work overruns the deadline. Fix /app/src/com/example/choreographer/DoFrameScheduler.kt to match the behavior below; leave Main.kt and FrameTypes.kt alone. The verifier compiles and runs it.

Operations come from /app/scenario.txt, one per line:
- SET_VSYNC_RATE <hz> sets the rate to 60, 90, or 120 (interval = 1000/hz ms, integer division). It applies at the end of the next DO_FRAME, so it first takes effect one frame later; that next frame keeps the current interval.
- POST_FRAME <token> <phase> <costMs> <repeat> registers a callback for the next frame. phase in {INPUT,ANIMATION,INSETS,TRAVERSAL}, repeat in {once,repeat}.
- REMOVE_FRAME <token> cancels a callback, both queued-for-next-frame and in-flight.
- POST_INPUT <eventTime> <x> <y> queues an input event at logical time eventTime.
- POST_MESSAGE <priority> <costMs> queues a Looper message; priority in {sync,async}.
- SCHEDULE_TRAVERSALS posts a sync barrier that blocks sync messages until the next frame's TRAVERSAL.
- DO_FRAME <vsyncTime> runs one frame.
- DRAIN_QUEUE <budgetMs> drains the queue outside a frame, up to budgetMs, with no partial dispatch.
- QUERY appends a snapshot to /app/output.txt.

Intervals: 60Hz is 16, 90Hz is 11, 120Hz is 8; start at 60Hz. For DO_FRAME <vsyncTime>, deadline is vsyncTime + frameIntervalMs. currentTime advances only by dispatched message costMs and executed callback costMs; phase transitions, queue checks, barrier lift, and rate changes cost nothing. At the start of each DO_FRAME, if currentTime is below vsyncTime it jumps to vsyncTime. The frame counter starts at one and increments each DO_FRAME.

A DO_FRAME runs in a fixed order. First, input resampling: events with eventTime <= vsyncTime-4 dispatch this frame and the rest defer; if any dispatched, emit INPUT_BATCH count=<n> oldestEventTime=<tOldest>, and if any deferred, emit INPUT_DEFERRED count=<n> (no time cost). Then INPUT callbacks run in posting order, each emitting FRAME_CALLBACK <token> and adding its costMs to currentTime. Between INPUT and ANIMATION it drains async: while currentTime < deadline, dispatch queued async FIFO, emit MSG_DISPATCH priority=async costMs=<n>, add costMs, and stop at the deadline or when no eligible async remains. ANIMATION callbacks run the same way, then another async drain, then INSETS callbacks, then another async drain. At the start of TRAVERSAL, emit MSG_BARRIER_LIFTED and mark the barrier inactive — every frame, whatever the prior state — then run TRAVERSAL callbacks the same way. After TRAVERSAL, a final drain: while currentTime < deadline, dispatch eligible messages — async FIFO always eligible, sync FIFO only when the barrier is inactive — emitting MSG_DISPATCH priority=<sync|async> costMs=<n>. If currentTime ever passes the deadline during the frame, that frame is jank: emit JANK frame=<n> overrunMs=<currentTime-deadline> once at the end. Work is never deferred because of jank.

Callbacks target the next frame, not the running one, and run in posting order within a phase. A once callback is removed after running; a repeat callback runs once per frame and re-registers at the end of its phase's next-frame queue. REMOVE_FRAME drops the token from the next-frame queue and in-flight, and during a frame also scrubs any re-registration a repeat callback would have produced.

Resampling detail: RESAMPLE_OFFSET is 4 ms; dispatch iff eventTime <= vsyncTime-4. Dispatched events coalesce into one INPUT_BATCH count=<n> oldestEventTime=<tMin>; deferred ones into one INPUT_DEFERRED count=<n>; (x,y) payloads aren't printed.

The queue has two FIFO lanes, sync and async. Barrier active: sync waits, async dispatches. Barrier inactive: both dispatch. SCHEDULE_TRAVERSALS posts a sync barrier and emits MSG_BARRIER; if a barrier is already active it's a no-op with no second MSG_BARRIER. Every DO_FRAME still emits MSG_BARRIER_LIFTED at TRAVERSAL start. DRAIN_QUEUE <budgetMs> dispatches up to budgetMs total cost with no partial dispatch (a message that won't fit is skipped); each step dispatches eligible async first, then eligible sync if the barrier is inactive, stopping when nothing fits, both lanes are empty, or the barrier blocks the rest.

SET_VSYNC_RATE records a pending interval applied at the end of the next DO_FRAME, so that frame keeps its current interval and deadline and the new interval applies on the following frame; a frame in progress keeps its interval and deadline. Emit VSYNC_RATE_CHANGED from=<oldHz> to=<newHz> when processed (no time cost).

QUERY appends:
  vsync rate=<hz> frameIntervalMs=<n> currentTime=<t>
  frames:
    frame=<n> vsyncTime=<t> deadlineMs=<t+interval> spentMs=<x> jank=<true|false>
      INPUT: <token>, ...
      ANIMATION: <token>, ...
      INSETS: <token>, ...
      TRAVERSAL: <token>, ...
    ...
  queue:
    sync=<n> async=<n> barrier=<active|inactive>
  next-frame callbacks:
    <token>, ...
  events:
    <event>
    ...
frames is cumulative in order; every phase line always prints (empty as PHASE: with no tokens), listing tokens that executed in that phase in dispatch order. queue shows current pending counts and barrier state. next-frame callbacks lists tokens registered for the next DO_FRAME across phases in registration order. events is the cumulative log in emission order: FRAME_CALLBACK <token>, INPUT_BATCH count=<n> oldestEventTime=<t>, INPUT_DEFERRED count=<n>, MSG_DISPATCH priority=<sync|async> costMs=<n>, MSG_BARRIER, MSG_BARRIER_LIFTED, JANK frame=<n> overrunMs=<x>, VSYNC_RATE_CHANGED from=<hz> to=<hz>.

Local debugging only, from /app: kotlinc src/com/example/choreographer/*.kt -include-runtime -d app.jar then java -jar app.jar scenario.txt output.txt.
