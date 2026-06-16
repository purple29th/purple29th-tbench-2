You're picking up a bug in the timer subsystem of a small event loop. The loop keeps a set of callbacks, each registered to run at some time, and a "tick" entry point the loop calls whenever it wakes up. A few things are going wrong in production: callbacks that were cancelled sometimes still run, re-arming the same timer seems to leave duplicates or run it twice, and repeating callbacks misbehave after the loop has been busy — they either fire in a burst to "catch up," or they slowly drift away from their intended schedule. Your job is to write the scheduler so it behaves correctly, then we'll run it against a batch of recorded operation logs.

The program reads operations from stdin, one per line:

- `SCHEDULE <id> <at>` — register callback `<id>` to run at time `<at>`.
- `SCHEDULE <id> <at> <every>` — same, but if `<every>` is a positive number the callback repeats with that period.
- `CANCEL <id>` — stop callback `<id>`.
- `FIRE_DUE <now>` — the loop just woke up at time `<now>`; run whatever is due.

`<id>` is a non-empty token; the times are non-negative integers. Print, one per line, the ids of the callbacks that actually ran, in the exact order they ran.

A few things about how it should behave:

When the loop fires at `<now>`, a callback is due if its time is less than or equal to `<now>`. If several are due in the same wake-up, run them earliest-time-first, and for callbacks with the same time, run them in the order they were first registered. A single wake-up only runs work that was already due when it began — anything that becomes due while the batch is running waits for the next `FIRE_DUE`.

A given id only ever has one pending timer. If you schedule an id that's already waiting, you don't get a second run — the existing timer is retargeted in place: it takes the earlier of its current time and the new one, adopts the period from the new request (a request with no period makes it a one-shot again), and keeps the place in the running order it had when it was first registered.

Cancellation is not immediate. A cancel takes effect at the start of the next `FIRE_DUE`, and when it does it clears the pending timer for that id — including one that was (re)scheduled after the cancel was requested but before that wake-up ran.

A repeating callback runs at most once per wake-up, no matter how long the loop was busy. After it runs at `<now>`, its next run is the first instant on its own period grid — its original time plus whole multiples of its period — that lands strictly after `<now>`. It does not replay each period it missed while the loop was asleep, and it stays anchored to its original schedule rather than drifting from the moment it happened to run.

Build your compiled executable to `/app/scheduler`. The grader runs it, feeds operations on stdin, and compares stdout to the expected firing order.
