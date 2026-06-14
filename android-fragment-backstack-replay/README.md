# codimango/android-fragment-backstack-replay

## Description

The agent works in a Kotlin project that simulates an Android-style FragmentManager: transactions add, replace, and remove fragments inside containers; transactions can be marked for the back stack with optional names; the back button (`POP`) reverses transactions; rotation (`ROTATE`) destroys the live state and replays the saved back stack to rebuild it. The current implementation has bugs in the back-stack replay, named-pop semantics, and replace-restore logic. The agent must fix `FragmentManager.kt` and `TransactionReplay.kt` so the simulation matches Android's actual behavior.

The task tests precise stateful reasoning across a real production bug pattern, not algorithmic cleverness. The traps are that `REPLACE` must remember what it replaced so `POP` can restore it, that named `POP` must remove every entry down to and including the named one, that `POP` for a name that doesn't exist on the back stack must be a no-op, that `ROTATE` must replay only back-stacked transactions, and that during replay a `REPLACE` against a now-empty container must behave like `ADD`.

## Completion Rates

Each run is `k=5` trials. A trial scores `1.0` only if all 12 verification scenarios pass.

| Model | Pass rate (k=5) |
|---|---|
| Oracle | 3/3 (1.00) deterministic |
| Avocado (`meta/avocado_dvsc_tester`) | measured by platform on submission |
| Opus 4.6 (`claude-opus-4-6`) | measured by platform on submission |

Calibration target: Avocado or Opus passes at least once and fails at least once across 5 trials.

## Model Analysis

Failure modes the task is designed to surface:

1. `REPLACE` doesn't track replaced fragments. Implementations that simply clear and add fail `pop_unnamed_restores_replaced`.
2. Named `POP` semantic confusion. Implementations that pop "up to but not including" or "until name found" fail `pop_named_drops_through`.
3. Missing-name `POP` mishandled. Implementations that error or pop everything fail `pop_missing_name_is_noop`.
4. `ROTATE` replays everything. Implementations that don't filter by `addToBackStack` fail `rotate_drops_non_backstacked`.
5. `REPLACE` on empty container after rotation. Implementations that early-return on empty fail `replace_on_empty_after_rotate`.

These reflect the bug class that ships in real Android apps: lost UI state on rotation, broken back-stack pop, wrong fragment shown after configuration change.

## Anti-Cheating Analysis

- Hardcoded outputs: scenarios use varied operation sequences whose expected outputs depend on the interaction of all four traps. A constant program cannot pass.
- Overfitting to visible tests: visible contract tests cover a subset of behaviors; hidden verifier scenarios stress edge cases absent from the visible set.
- Modifying test files: tests run from `/tests`, copied in by the harness after the agent finishes. The reward is written by `tests/test.sh`, outside the agent's control.
- Bypassing the intended solution path: the only way to pass all 12 scenarios is to implement correct back-stack replay, named-pop, and replace-restore semantics. The Dockerfile ships only JDK + Kotlin compiler.
