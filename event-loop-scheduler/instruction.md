You're picking up a bug in the timer subsystem of a small event loop. The loop keeps a set of callbacks, each registered to run at some time, and a "tick" entry point the loop calls whenever it wakes up. A few things are going wrong in production: callbacks that were cancelled sometimes still run, re-arming the same timer leaves duplicates or runs it twice, repeating callbacks either burst to "catch up" or drift off schedule after the loop has been busy, and when a single wake-up has a lot of work queued it blows past the time budget the loop is allowed per tick instead of spilling the overflow to the next wake-up. Write the scheduler so it behaves correctly, then we'll run it against a batch of recorded operation logs.

The program reads operations from stdin, one per line:

- `SCHEDULE <id> <at>` — register callback `<id>` to run at time `<at>`.
- `SCHEDULE <id> <at> <every>` — same, but if `<every>` is positive the callback repeats with that period.
- `SCHEDULE <id> <at> <every> <cost>` — same, and the callback costs `<cost>` units of work to run (default 1; use `<every>` of 0 for a one-shot with a custom cost).
- `CANCEL <id>` — stop callback `<id>`.
- `BUDGET <n>` — from now on, a single wake-up may run at most `<n>` total units of work. With no `BUDGET` set, a wake-up runs everything that's due.
- `FIRE_DUE <now>` — the loop just woke up at time `<now>`; run whatever is due.

`<id>` is a non-empty token; the numbers are non-negative integers. Print, one per line, the ids of the callbacks that actually ran, in the exact order they ran.

How it should behave:

When the loop fires at `<now>`, a callback is due if its time is less than or equal to `<now>`. Due callbacks run earliest-time-first, and ties (same time) run in the order they were first registered. A single wake-up only runs work that was already due when it began.

If a budget is in force, walk the due callbacks in that order and keep running them while the running total of their costs stays within the budget. The first callback that would push the total over the budget does not run — and neither does anything after it; they all wait for the next wake-up (so a single expensive callback at the front can hold up cheaper ones behind it). Costs only gate running; they don't change a callback's time or order.

A given id only ever has one pending timer. Scheduling an id that's already waiting doesn't add a second run — the existing timer is retargeted in place: it takes the earlier of its current and new time, adopts the new request's period and cost, and keeps the place in the running order it had when first registered.

Cancellation isn't immediate. A cancel takes effect at the start of the next `FIRE_DUE` and clears the pending timer for that id, including one (re)scheduled after the cancel but before that wake-up ran.

A repeating callback runs at most once per wake-up, however long the loop was busy. After it runs at `<now>`, its next run is the first instant on its own period grid — original time plus whole multiples of its period — strictly after `<now>`. It does not replay each missed period, and it stays anchored to its original schedule rather than drifting from when it happened to run.

Build your compiled executable to `/app/scheduler`. The grader runs it, feeds operations on stdin, and compares stdout to the expected firing order.
