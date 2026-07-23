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
| heldout_3 | 10000 | 96 | ~1929 | **12000** | dense reachable SCC is the answer; count trap 200 node SCC 11800; unreachable SCC 30000; **1600 long chain** (recursive DFS dies at the default limit); 20 sub threshold islands; root in cycle |
| heldout_4 | 10000 | 64 | ~60 | **10000** | winner sits **exactly at threshold**; a 9999 island just under; a 9500 count trap (also sub threshold); unreachable island 14000; root in cycle |
| heldout_5 | 0 | 96 | ~15 | **3500** | winner is a **singleton** (3500, beats a 3200 and 2700 cycle); negative heavy cycle (5000 + -4000); unreachable island 9000; root in cycle; self loop |

Each plausible but wrong strategy fails on at least one held out (verified by the
bundled harness against the reference):

| Wrong strategy | Fails on |
|----------------|----------|
| pick by node count | heldout_1, heldout_3, heldout_5 |
| include root value | all five |
| ignore reachability | all five |
| threshold with `>` instead of `>=` | heldout_2, heldout_4 |
| ignore singleton islands | heldout_1, heldout_5 |
| recursive DFS (default limit) | heldout_3 (RecursionError on the 1600 chain) |

## Completion Rates

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; all 7 verifier tests pass) |
| Frontier models | `metacode` / `claude-code` | to be measured by the validation pipeline |

> **Calibration target:** the previous version was too easy because the held outs
> were large but sparse (one trap each, reducing to "max reachable node"). There
> are now five held outs stacking six independent trap types, and the verifier
> requires every one to pass, so a trial that slips on any single trap fails. The
> dominant expected failure modes are including the root value, counting nodes
> instead of summing weight, missing that the winner can be a singleton or sit
> exactly at the threshold, and recursion on the long chain. Note: because the
> problem is fully specified (a strongly connected component computation), a
> flawless implementation passes 5/5 by design; the difficulty comes from the
> number of independent edge cases a trial must get right at once.

## Anti Cheating

- **Hardcoded outputs:** the five held outs have different answers (2600, 610,
  12000, 10000, 3500), thresholds (0, 610, 10000), offsets (64, 96) and sizes,
  and all differ from the visible sample (220). A constant cannot satisfy them.
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
