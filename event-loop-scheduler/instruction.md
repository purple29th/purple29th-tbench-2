You're finishing the timer subsystem of a small event loop. The loop keeps a set of callbacks, each registered to run at a time, and a "tick" entry point the loop calls when it wakes up. Recent production reports: cancelled callbacks sometimes still run, re-arming a timer leaves duplicates or double-runs it, repeating callbacks drift or fire in catch-up bursts, and under load the loop spends more work per wake-up than it should. Write the scheduler so it behaves correctly, then we run it against recorded operation logs.

The program reads operations from stdin, one per line:

- `SCHEDULE <id> <at>` — register callback `<id>` to run at time `<at>` (cost 1, one-shot).
- `SCHEDULE <id> <at> <every>` — same, but if `<every>` is positive the callback repeats with that period.
- `SCHEDULE <id> <at> <every> <cost>` — same, with an explicit integer `<cost>` (credits) to run it; use `<every>` 0 for a one-shot with a cost.
- `CANCEL <id>` — stop callback `<id>`.
- `BUDGET <num> <den> <cap>` — the loop runs on a work budget (see below).
- `FIRE_DUE <now>` — the loop woke up at time `<now>`; run whatever is due and affordable.

`<id>` is a non-empty token; times, periods, costs and budget fields are non-negative integers. Print, one per line, the ids of the callbacks that actually ran, in the exact order they ran.

Behaviour:

A callback is due at a wake-up when its time is `<= now`. When several are due, run them earliest-time-first; break ties between same-time callbacks by registration order (the one waiting longest goes first). A wake-up only runs work that was already due when it began — anything that becomes due while the batch runs waits for the next `FIRE_DUE`.

A given id has at most one pending timer. Re-scheduling an id that's already waiting does not create a second run: the existing timer is retargeted in place — it takes the earlier of its current and new time, adopts the new period and cost, and keeps the place in the running order it had when first registered.

Cancellation is not immediate: a cancel takes effect at the start of the next `FIRE_DUE`, clearing the pending timer for that id (including one re-scheduled after the cancel but before that wake-up).

A repeating callback runs at most once per wake-up. After it runs at `<now>`, its next run is the first instant on its own period grid — its anchor time plus whole multiples of its period — strictly after `<now>`. It never replays periods missed while the loop slept, and stays anchored to its schedule rather than drifting from when it happened to run.

The work budget (only when a `BUDGET` op has been seen): the budget gains `<num>/<den>` credits per millisecond of elapsed time and accrues **continuously** between wake-ups — it is a single running quantity, not recomputed from scratch each tick. It never exceeds `<cap>` credits. At a wake-up, after the budget has been brought up to date for the elapsed time, run the due callbacks in priority order, paying each one's cost from the budget. When the next due callback in order cannot be afforded, the wake-up stops there — it does not skip ahead to a cheaper callback behind it. Callbacks left unrun stay pending and are reconsidered at the next wake-up. With no `BUDGET` op, treat the budget as unlimited.

Build your compiled executable to `/app/scheduler`. The grader runs it, feeds operations on stdin, and compares stdout to the expected firing order.
