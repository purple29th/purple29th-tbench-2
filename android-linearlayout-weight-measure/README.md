# codimango/android-linearlayout-weight-measure

## Description

Kotlin simulator of a horizontal layout measure pass: divide available width across FIXED, WRAP, and WEIGHT children and lay them out left to right. The distribution rule is inverse-weight — weighted children share the leftover in proportion to their complement (totalWeight minus own weight) — which inverts the usual proportional-to-weight intuition. The agent fixes LinearLayoutMeasurer.kt so measured widths, leftover, overflow, and layout positions match the spec across seven scenarios.

## Completion Rates

| Model                              | Pass rate (k=5)                    |
|------------------------------------|------------------------------------|
| Oracle                             | 3/3 (1.00) deterministic           |
| Avocado (meta/avocado_dvsc_tester) | measured by platform on submission |
| Opus 4.6 (claude-opus-4-6)         | measured by platform on submission |

## Model Analysis

1. Inverse-weight distribution. Space is divided in proportion to (totalWeight - own weight), so a larger weight yields a smaller width. Implementations that use the canonical proportional-to-weight split invert every weighted child's width.
2. Weight divides the leftover (distributable) space, not the total width.
3. Integer-division remainder goes to the last weighted child so the row fills exactly; flooring every share loses pixels.
4. Margins count toward used width in the first pass; ignoring them inflates leftover and the weighted widths.
5. Negative leftover clamps distributable to 0; layout start positions compound, so any width error shifts every later child.

## Anti-Cheating Analysis

- Seven per-behavior scenarios under /tests/expected/, mounted only at verifier time.
- Verifier compiles the agent's source via kotlinc and runs each scenario; reward is all-or-nothing per scenario.
- Reference solution implements the exact inverse-weight integer arithmetic and is never agent-readable.
