# codimango/android-theme-cascade

## Description

The agent works in an Android-style Kotlin/Gradle multi-module project (`:app`, `:core-ui`, `:theme`) with a buggy theme cascade resolver. Several unit tests are failing. The agent must fix `theme/src/main/kotlin/com/example/theme/ThemeResolver.kt` so that the resolver correctly handles theme inheritance, component overrides, state-conditional overrides, and the distinction between `apply()`-bound components and components that follow the active theme. Running the app with a provided scenario must produce a deterministic `/app/output.json` with resolved tokens for each `(component, state)` query.

The task tests precise stateful reasoning across a real-looking codebase rather than algorithmic cleverness. The traps are that the cascade order must be base-theme to specific (theme chain → component override → state override), that state overrides must apply only when the requested state matches, and that `switchActiveTheme()` must NOT rebind components that have an explicit `apply()` binding. Models that flip the cascade direction, apply all state overrides unconditionally, or rebind every component on theme switch will fail subtle test scenarios.

## Completion Rates

Each run is `k=5` trials. A trial scores `1.0` only if all verification tests pass.

| Model | Pass rate (k=5) |
|---|---|
| Oracle | 3/3 (1.00) deterministic |
| Avocado (`meta/avocado_dvsc_tester`) | measured by platform on submission |
| Opus 4.6 (`claude-opus-4-6`) | measured by platform on submission |

Calibration target: Avocado or Opus passes at least once and fails at least once across 5 trials.

## Model Analysis

Failure modes the task is designed to surface:

1. Cascade direction inverted — applying state override first then theme on top, which lets parent theme tokens overwrite component-level overrides. Fails `state_override_beats_component_override` and `deep_inheritance_three_levels`.
2. State overrides applied unconditionally — merging every state override into every resolution regardless of requested state. Fails `default_state_unaffected_by_pressed_override`.
3. `switchActiveTheme()` rebinding `apply()`-bound components — walking every tracked component and changing its theme binding to the new active theme. Fails `explicit_apply_survives_switch` and `explicit_apply_through_two_switches`.
4. Mixing apply and unbound components incorrectly — treating bound and unbound the same after a switch. Fails `mixed_apply_and_unbound`.

These reflect reasoning gaps about layered theme cascades and the semantic difference between active-theme membership and explicit theme binding — the kind of distinction that separates engineers who have actually shipped Android theming from those who pattern-match on "implement an override resolver."

## Anti-Cheating Analysis

- Hardcoded outputs: the agent's app reads a JSON scenario from `/app/scenario.json` and emits resolved tokens to `/app/output.json`. Tests use 12 distinct scenarios whose outputs depend on inheritance depth, override interaction, and apply-vs-switch timing — a constant program cannot pass.
- Overfitting to visible tests: the visible unit tests in `theme/src/test/` cover a subset of behaviors. The hidden verifier scenarios in `tests/expected/` are mounted only at verification time and stress edge cases (multi-switch, three-level inheritance, mixed apply/unbound) not present in the visible tests.
- Modifying test files: tests run from `/tests`, copied in by the harness after the agent finishes. The reward is written by `tests/test.sh`, outside the agent's control.
- Bypassing the intended solution path: the only way to produce correct output across the 12 distinct scenarios is to actually fix the resolver semantics. The Dockerfile ships only the JDK + Gradle + Kotlin compiler — no reference implementation, no `tests/`, no expected outputs.
