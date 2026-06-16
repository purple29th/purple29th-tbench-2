# codimango/event-loop-scheduler

## Description

A C++ event-loop timer scheduler driven by SCHEDULE / CANCEL / BUDGET / FIRE_DUE on stdin, printing the order callbacks fire. The scheduler coalesces to one pending timer per id, defers cancellation to round boundaries, never runs same-round new work, supports repeating callbacks with period-aligned catch-up, and enforces a per-wake-up cost budget with defer-whole-on-overflow.

## Completion Rates

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

1. Per-round cost budget — walk due callbacks in order, run while the cumulative cost stays within budget; the first that would exceed it (and everything after) defers to the next wake-up. A single expensive front callback blocks cheaper ones behind it. Naive impls skip-and-continue (running the cheaper ones) or have no budget at all.
2. Coalescing — one pending timer per id; a re-schedule retargets in place (earlier time, new period and cost, original order position).
3. Deferred cancel — applies at the next FIRE_DUE; clears the pending timer including a post-cancel re-schedule.
4. No same-round new work; firing order ascending time then first-registration.
5. Recurring fire-once + period-grid re-alignment (no catch-up storm, no drift).

## Anti-Cheating Analysis

- Hidden stdin operation logs feed the compiled binary; stdout is diffed exactly. Interleaved budget/coalesce/cancel/recurring cases defeat a constant program.
- Tests run from /tests, copied in by the harness after the agent finishes; reward written by tests/test.sh.
- The Dockerfile ships only a C++ toolchain — no reference implementation, no tests, no expected outputs.
