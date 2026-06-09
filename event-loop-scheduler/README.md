# codimango/event-loop-scheduler

## Description

The agent must implement a C++ program (`/app/scheduler`) that simulates a single-threaded event-loop scheduler processing `SCHEDULE`, `CANCEL`, and `FIRE_DUE` operations from stdin and prints the fire order of callback IDs to stdout. The scheduler uses absolute monotonic times provided in `FIRE_DUE` events as its notion of "now"; `SCHEDULE` and `CANCEL` carry no time of their own.

The task tests precise stateful reasoning rather than algorithmic cleverness. The traps are that **cancellation is queued, not immediate** — `CANCEL` requests apply at the start of the next `FIRE_DUE`, so a callback already in the ready set when that `FIRE_DUE` begins still fires this round if its cancel arrived after the round started. There is no closed-form shortcut; the agent must faithfully model deferred cancellation and the round-boundary semantics that follow from it.

## Completion Rates

Each run is `k=5` trials. A trial scores `1.0` only if **all** verification tests pass.

| Model | Pass rate (k=5) |
|---|---|
| Oracle | 3/3 (1.00) deterministic |
| Avocado (`meta/avocado_dvsc_tester`) | measured by platform on submission |
| Opus 4.6 (`claude-opus-4-6`) | measured by platform on submission |

**Calibration target:** Avocado **or** Opus passes at least once and fails at least once across 5 trials.

## Model Analysis

Failure modes the task is designed to surface:

1. **Immediate cancellation** — Models that treat `CANCEL` as "remove from priority queue right now" produce the wrong fire order on `cancel_queued_for_next_round`. The cancel must be queued and applied at the start of the *next* `FIRE_DUE`.
2. **Mishandled tie-breaking** — Two callbacks scheduled for the same time must fire in schedule order (FIFO). Models that use a plain `std::priority_queue` keyed only by time get nondeterministic order on `tie_breaking`.
3. **Lost re-schedules** — When the same id is cancelled then re-scheduled before the next `FIRE_DUE`, the queued cancel must purge *all* pending entries for that id, including the new one. Models that only purge the original entry get `cancel_then_reschedule_same_id` wrong.
4. **Across-round confusion** — Models that don't separate "what happens during a fire round" from "what happens between rounds" fail `cancel_across_rounds` or `schedule_after_fire_due`.

These reflect reasoning gaps about event-loop boundary semantics, not task-setup issues. The environment is deterministic (oracle 3/3) and the C++ entrypoint is unambiguous.

## Anti-Cheating Analysis

- **Hardcoded outputs:** The oracle (`solution/scheduler.cpp`) implements a real simulation. Tests use varied operation sequences whose outputs cannot be predicted without faithfully modelling deferred cancellation, FIFO tie-breaking, and ready-set snapshots — a constant program cannot pass.
- **Overfitting to visible tests:** Test inputs and expected outputs live in `tests/test_outputs.py`, mounted at verification time and hidden from the agent. The program must read arbitrary stdin, so special-casing hidden inputs is impossible.
- **Modifying test files:** Tests run from `/tests`, copied in by the harness after the agent finishes. The reward is written by `tests/test.sh`, outside the agent's control.
- **Bypassing the intended solution path:** The only way to produce correct output across the 12 distinct operation streams is to implement the actual deferred-cancellation event-loop simulation. The Dockerfile ships only a C++ toolchain — no reference implementation, no `tests/`, no expected outputs.
