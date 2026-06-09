# What you're building

Write a small C++ program that simulates an event-loop scheduler. It schedules callbacks, cancels them, and fires the ones that are due.

# Input (stdin)

One operation per line:

- `SCHEDULE <id> <at_ms>` — schedule callback `<id>` to run at absolute time `<at_ms>`.
- `CANCEL <id>` — request cancellation of `<id>` if it has not fired.
- `FIRE_DUE <now_ms>` — the loop wakes up at time `<now_ms>` and fires callbacks that are due.

`<id>` is a non-empty token; `<at_ms>` and `<now_ms>` are non-negative integers.

# Output (stdout)

Print the IDs of callbacks that actually fired, one per line, in the exact order they fired.

# Two important rules

- **Cancels are deferred.** `CANCEL` requests do not apply immediately. They take effect at the start of the next `FIRE_DUE`.
- **No same-round "new work".** A `FIRE_DUE` round only fires callbacks that were already due at the moment the round began. New callbacks scheduled while the round is firing wait for a later `FIRE_DUE`.

# Build target

Your compiled executable must be at `/app/scheduler`. The grader runs `/app/scheduler`, feeds operations on stdin, and compares stdout to expected output.
