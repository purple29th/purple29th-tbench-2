# codimango/mobile-config-exposure-imbalance

## Description

From scratch Python script (`/app/solve.py`, standard library only) that parses a
custom Android mobile config binary (`.mcfg`) and prints the total weight of the
most concentrated reachable mutual dependency island that passes the exposure
threshold. Built in the mold of `mri-volume-calc` and `android-depth-object-volume`:
the concentrated core (a strongly connected group of configs) has to be picked out
from scattered distractor islands, the way a tumor core is picked out from spread
pixel noise.

A mutual dependency island is a strongly connected component: a set of config ids
where every id reaches every other following directed dependency edges (a single
node counts as an island). The answer is the reachable island with the largest
total value, with the root value excluded and the exposure threshold applied.

## Why it is hard

A correct solution needs iterative reachability from root 0, hand written
strongly connected component labeling, root value exclusion, a `>=` threshold
filter, and a max by total weight (not node count). It is fully specified, so the
difficulty comes from stacking many independent traps into each held out file: a
trial has to get every one right, and each additional trap it slips on flips the
result. The held outs deliberately concentrate on the edge cases the instruction
does not belabor.

## Held out traps (measured)

Ground truth is recomputed independently in the verifier with a Tarjan lowlink
walk (different traversal order than the solution). Answers below are the verified
oracle == reference values.

| File | thr | offset | nodes | answer | traps stacked |
|------|-----|--------|-------|--------|---------------|
| heldout_1 | 0 | 64 | ~20 | **2600** | winner is a **singleton** (beats a 2500 cycle); count trap 5 node cycle 2400; unreachable 4 cycle 9000; root in cycle (incl root 50090); dangling deps; self loop |
| heldout_2 | 610 | 96 | ~16 | **610** | winner sits **exactly at threshold** (a `>` comparison drops it to 0); a 600 island just under; negative valued member; root in cycle (incl root 100009); unreachable island 20000 |
| heldout_3 | 10000 | 96 | ~1889 | **12000** | dense reachable SCC is the answer; count trap 200 node SCC 11800; unreachable SCC 30000; **1500 long chain** (recursion dies); 40 sub threshold islands; root in cycle |

Each plausible but wrong strategy fails on at least one held out (verified by the
bundled harness against the reference):

| Wrong strategy | Fails on |
|----------------|----------|
| pick by node count | heldout_1 (2400 vs 2600), heldout_3 (11800 vs 12000) |
| include root value | all three |
| ignore reachability | all three |
| threshold with `>` instead of `>=` | heldout_2 (0 vs 610) |
| ignore singleton islands | heldout_1 (2500 vs 2600) |
| recursive DFS (default limit) | heldout_3 (RecursionError on the 1500 chain) |

## Completion Rates

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; all 5 verifier tests pass) |
| Frontier models | `metacode` / `claude-code` | to be measured by the validation pipeline |

> **Calibration target:** the previous version was too easy because the held outs
> were large but sparse (one trap each, reducing to "max reachable node"). The
> hardened held outs stack six independent trap types, so a trial that gets any one
> wrong fails. The dominant expected failure modes are including the root value,
> counting nodes instead of summing weight, missing that the winner can be a
> singleton or sit exactly at the threshold, and recursion on the long chain.

## Anti Cheating

- **Hardcoded outputs:** the three held outs have different answers (2600, 610,
  12000), thresholds (0, 610, 10000), offsets (64, 96, 96) and sizes, and all
  differ from the visible sample (220). A constant cannot satisfy them.
- **Overfitting to visible tests:** the only data in the container is the sample
  scan; held outs live under `tests/` and are absent during the agent run.
- **Modifying test files:** tests and data are copied in only at verify time; the
  reward is computed by the verifier from an independent Tarjan reference, not from
  anything the agent can edit. `tests/_gen.py` (the deterministic data generator)
  is co-located with the tests and never ships in the agent container.
- **Bypassing the intended path:** `test_from_scratch()` rejects numpy, scipy,
  networkx, igraph, pandas and shelling out (`subprocess`, `os.system`,
  `os.popen`, `__import__`, `importlib`, `eval`, `exec`), forcing genuine byte
  parsing and a hand written SCC labeller.

Inspired by https://github.com/codimango/mehag-tbench/tree/main/mri-volume-calc
and https://github.com/codimango/purple29th-tbench-2/tree/main/android-depth-object-volume.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
