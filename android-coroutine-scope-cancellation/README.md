# codimango/android-coroutine-scope-cancellation

## Description

Kotlin simulator of structured-concurrency Job hierarchies (the model behind CoroutineScope / viewModelScope / lifecycleScope). Jobs form a tree; cancellation propagates to descendants, a child failure cancels siblings and fails the parent up the chain, a SupervisorJob absorbs failures at its boundary, and AWAIT introduces a COMPLETING state with a completion cascade that fires as the last child finishes. The agent fixes StructuredScope.kt so the job table and event log match expectations across complete, cancel-propagation, supervisor-absorb, failure-propagation, await-cascade, and await-then-fail scenarios.

## Completion Rates

Each run is k=5 trials. A trial scores 1.0 only if every scenario's output matches its expected file exactly.

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

Failure modes the task surfaces:

1. Cancellation must reach the whole subtree, not just the named job.
2. A child failure in a normal scope cancels siblings AND fails the parent, then propagates up.
3. A SupervisorJob absorbs a child failure: siblings and the supervisor stay alive.
4. The ancestor chain inherits FAILED (carrying the exception), not CANCELLED — counter to the naive "everything downstream of a failure is cancelled" model, and it applies to a COMPLETING parent too.
5. AWAIT introduces COMPLETING (non-terminal) and a completion cascade: a parent in COMPLETING auto-completes only when its last non-terminal child finishes, cascading up through chained COMPLETING ancestors.
6. COMPLETE and AWAIT are both gated on having no non-terminal children (join semantics).

## Anti-Cheating Analysis

- Six per-behavior scenarios under /tests/expected/, mounted only at verifier time.
- Verifier compiles the agent's source via kotlinc and runs each scenario; reward is all-or-nothing per scenario.
- Reference solution implements every rule honestly and is never agent-readable.
