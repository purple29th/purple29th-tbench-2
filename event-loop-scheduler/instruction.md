You're picking up a bug in the timer subsystem of a small event loop. The loop keeps a set of callbacks, each registered to run at some time, and a "tick" entry point the loop calls when it wakes up. Several things are going wrong in production: cancelled callbacks sometimes still run; re-arming the same timer leaves duplicates or runs it twice; repeating callbacks either burst to "catch up" or drift off schedule after the loop has been busy; a busy wake-up blows past its per-tick work budget instead of spilling the overflow to the next wake-up; and "follow-up" callbacks that are supposed to run only after another callback fires are running at the wrong time, or even when their trigger never ran. Write the scheduler so it behaves correctly, then we'll run it against a batch of recorded operation logs.

The program reads operations from stdin, one per line:

- `SCHEDULE <id> <at>` — register `<id>` to run at time `<at>`.
- `SCHEDULE <id> <at> <every>` — same, but if `<every>` is positive the callback repeats with that period.
- `SCHEDULE <id> <at> <every> <cost>` — same, with a per-run work cost (default 1; use `<every>` of 0 for a one-shot with a custom cost).
- `AFTER <id> <dep> <delay>` — register `<id>` as a follow-up: it has no time of its own until `<dep>` actually fires, at which point `<id>` is scheduled to run `<delay>` after that.
- `CANCEL <id>` — stop callback `<id>`.
- `BUDGET <n>` — from now on a wake-up may run at most `<n>` total units of work.
- `FIRE_DUE <now>` — the loop woke up at time `<now>`; run whatever is due.

`<id>` and `<dep>` are non-empty tokens; the numbers are non-negative integers. Print, one per line, the ids of the callbacks that actually ran, in the exact order they ran.

How it should behave:

When the loop fires at `<now>`, a callback is due if its time is less than or equal to `<now>`. Due callbacks run earliest-time-first. To break a tie between same-time callbacks, run them in the order they entered the pending set — the one waiting longest goes first. A plain re-schedule of an already-pending id keeps that id's original waiting position, but a repeating callback re-enters the pending set fresh each time it re-arms, so a just-re-armed timer is the newest waiter and sorts behind anything already waiting. A wake-up only runs work that was already due when it began; anything that becomes pending while the batch runs waits for a later wake-up.

If a budget is in force, walk the due callbacks in order and keep running them while the running cost total stays within budget. The first that would exceed the budget does not run, and neither does anything after it — they wait for the next wake-up, so an expensive callback at the front can hold up cheaper ones behind it. Costs only gate running; they don't change a callback's time or order.

A follow-up registered with `AFTER` is dormant until its trigger actually runs. When the trigger fires at `<now>`, the follow-up is scheduled at `<now>` plus its delay — and since that scheduling happens while the wake-up is in progress, the follow-up is new work that waits for a later wake-up. A trigger that never runs — because it was cancelled, or never became due, or was held back by the budget — never schedules its follow-up. A trigger that repeats re-schedules its follow-up each time it fires.

A given id only ever has one pending timer. Scheduling (or triggering) an id that's already waiting doesn't add a second run — the existing timer is retargeted in place to the earlier of its current and new time and adopts the new period and cost.

Cancellation isn't immediate. A cancel takes effect at the start of the next `FIRE_DUE` and clears the pending timer for that id, including one (re)scheduled after the cancel but before that wake-up ran.

A repeating callback runs at most once per wake-up. After it runs at `<now>`, its next run is the first instant on its own period grid — original time plus whole multiples of its period — strictly after `<now>`. It does not replay missed periods and does not drift from when it happened to run.

Build your compiled executable to `/app/scheduler`. The grader runs it, feeds operations on stdin, and compares stdout to the expected firing order.
