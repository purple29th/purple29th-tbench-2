# codimango/event-loop-scheduler

## Description

A C++ event-loop timer scheduler driven by SCHEDULE / CANCEL / FIRE_DUE operations on stdin, printing the order callbacks fire. The scheduler coalesces to one pending timer per id, defers cancellation to round boundaries, never runs same-round new work, and supports repeating callbacks with period-aligned catch-up. The agent must implement the firing order, coalescing, deferred cancel, and recurring re-arm semantics so the compiled binary's stdout matches the expected firing order.

## Completion Rates

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

1. Coalescing — one pending timer per id; a re-schedule retargets in place to the earlier time, adopts the new request's period (none = one-shot), and keeps the original running-order position. Naive implementations duplicate the timer, take the latest time, or move it to the back of the order.
2. Deferred cancel — applies at the start of the next FIRE_DUE and clears the pending timer, including one (re)scheduled after the cancel but before it applied.
3. No same-round new work — a wake-up only runs callbacks already due when it began.
4. Firing order — ascending scheduled time, ties broken by first-registration order.
5. Recurring fire-once — a repeating callback overdue by several periods runs only once per wake-up, not once per missed period.
6. Period-grid re-alignment — re-arms to the original-time-plus-k*period grid, first slot strictly greater than now (no drift from actual run time).

## Anti-Cheating Analysis

- Hidden stdin operation logs feed the compiled binary; stdout is diffed exactly. The interleaved coalesce/cancel/recurring cases defeat a constant program.
- Tests run from /tests, copied in by the harness after the agent finishes; reward written by tests/test.sh.
- The Dockerfile ships only a C++ toolchain — no reference implementation, no tests, no expected outputs.
