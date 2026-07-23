# codimango/mobile-config-exposure-imbalance

## Description

From scratch Python script (`/app/solve.py`, standard library only) that parses a
custom Android mobile config binary (`.mcfg`) and prints the **minimum number of
configs that must be turned on to reach the maximum total exposure**.

Each config has a **signed** exposure delta (positive = adds exposure, negative =
costs exposure). Turning a config on forces on every config it depends on
(transitively). A set of configs that respects this is a valid rollout. First
find the highest total exposure any valid rollout can reach; then, among all
rollouts that reach it, report the size of the smallest one. The empty rollout
(exposure 0, size 0) is always allowed.

## Why it is hard (and not a one-pass recall)

The number that a memorised "best set of dependent items with signed profits"
snippet produces is the **exposure value** -- which is *not* the answer here. The
task needs two composed steps, and the second is the subtle one:

1. **Find the best achievable exposure.** You cannot just sum the positive
   configs (a positive config can force in costly negative dependencies you
   cannot avoid) and you cannot turn everything on (that pays avoidable costs).
   This step is a flow/cut optimisation over the dependency graph.
2. **Find the smallest rollout that reaches that maximum.** Several rollouts can
   tie for the best exposure: any config whose forced cost exactly cancels its
   benefit can be added or dropped without changing the total. The minimal
   rollout must leave every such **zero-gain padding** config out. Reading it off
   the residual graph (configs still reachable from the source after the max flow)
   gives the unique smallest optimal rollout.

Reporting the exposure value, counting all positive configs, or taking the
*largest* optimal set (which keeps the zero-gain padding) all give wrong answers.

## Held out cases (measured)

Ground truth is recomputed independently in the verifier with a **different**
max-flow implementation than the oracle, then the smallest optimal rollout is read
off the residual graph. Answers below are verified oracle == reference; the small
ones are also confirmed by exhaustive brute force over all valid rollouts.

| File | offset | nodes | answer (min rollout size) | what it exercises |
|------|--------|-------|---------------------------|-------------------|
| heldout_1 | 64 | ~11 | **6** | worth-it vs not-worth-it configs, a forced 3-config chain, and a zero-gain pad that must be excluded |
| heldout_2 | 96 | ~7 | **5** | a net-negative dependency **cycle** pulled in by a high-value config, plus a zero-gain pad |
| heldout_3 | 96 | ~1400 | **650** | scale: 250 worth-it gadgets + 150 free positives kept; 250 not-worth-it + 100 zero-gain pads dropped |
| heldout_4 | 96 | ~6 | **0** | every positive depends on a strictly costlier config, so the best rollout is empty |
| heldout_5 | 96 | ~21 | **2** | one worth-it pair plus ten zero-gain pads that a padded rollout of 22 configs would keep at the same exposure |

Obvious-but-wrong strategies (verified against the reference):

| Wrong strategy | heldout_1 | heldout_3 | heldout_5 |
|----------------|-----------|-----------|-----------|
| correct answer (min rollout size) | 6 | 650 | 2 |
| print the maximum exposure value | 220 | 28201 | 70 |
| count every positive config | 5 | 750 | 11 |
| keep the largest optimal set (with padding) | 8 | 850 | 22 |

## Completion Rates

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; all 7 verifier tests pass) |
| Frontier models | `metacode` / `claude-code` | to be measured by the validation pipeline |

> **Calibration target:** an earlier version asked only for the best exposure
> value, which strong models recalled and solved 5/5. Asking instead for the
> minimum rollout size composes a well-known first step with a much less commonly
> recalled second step (the minimal optimal set via residual reachability), so a
> recalled snippet that stops at the value fails, and getting the minimal set
> right from scratch is where trials diverge.

## Anti Cheating

- **Hardcoded outputs:** the five held outs have different answers (6, 5, 650, 0,
  2), offsets (64, 96) and sizes; all differ from the visible sample (3). A
  constant cannot satisfy them.
- **Overfitting to visible tests:** the only data in the container is the sample
  file; held outs live under `tests/` and are absent during the agent run.
- **Modifying test files:** tests and data are copied in only at verify time; the
  reward is computed with an independent max-flow implementation different from the
  oracle's, so it never trusts a value baked into the agent's script.
  `tests/_gen.py` (the deterministic generator) is co-located with the tests and
  never ships in the agent container.
- **Bypassing the intended path:** `test_from_scratch()` rejects numpy, scipy,
  networkx, igraph, pandas (which ship graph / max-flow routines) and shelling
  out, forcing a hand-written parser and flow computation.

Inspired by https://github.com/codimango/mehag-tbench/tree/main/mri-volume-calc
and https://github.com/codimango/purple29th-tbench-2/tree/main/android-depth-object-volume.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
