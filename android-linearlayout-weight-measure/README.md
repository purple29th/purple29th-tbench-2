# codimango/android-linearlayout-weight-measure

## Description

Kotlin simulator of Android's horizontal LinearLayout measure pass with minimum-width weight redistribution: divide available width across FIXED, WRAP, and WEIGHT children, then iteratively pin any weighted child squeezed below its minimum and recompute the rest. The agent fixes LinearLayoutMeasurer.kt so measured widths, leftover, overflow, minimum-width redistribution, and layout positions match Android's integer arithmetic across seven scenarios.

## Completion Rates

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

1. Weight divides the LEFTOVER space, not the total width — the canonical LinearLayout bug.
2. Integer-division remainder goes to the last active weighted child so the row fills exactly; flooring every share loses pixels.
3. Margins count toward used width in the first pass.
4. Minimum-width redistribution is iterative: pinning one child below its minimum changes the divisor and the leftover for everyone else, so a single pass is wrong — the redistribution must repeat until stable.
5. A pinned child keeps its minWidth even when that exceeds the space available.
6. Negative leftover clamps distributable to 0; layout start positions compound, so any width error shifts every later child.

## Anti-Cheating Analysis

- Seven per-behavior scenarios under /tests/expected/, mounted only at verifier time.
- Verifier compiles the agent's source via kotlinc and runs each scenario; reward is all-or-nothing per scenario.
- Reference solution implements the exact iterative integer arithmetic and is never agent-readable.
