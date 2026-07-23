# codimango/mobile-config-exposure-imbalance

## Description

From scratch Python script (`/app/solve.py`, standard library only) that parses a
custom Android mobile config binary (`.mcfg`) and prints the maximum total
exposure of a valid config activation set.

Each config has a **signed** exposure weight (positive = benefit, negative =
cost). You may activate any set of configs, but if you activate a config you must
also activate every config it depends on (transitively). Among all valid
activation sets, report the largest total weight. The empty set (0) is always
allowed, and if the best total is below the header threshold the answer is 0.

## The insight (why it is hard)

This is the **maximum-weight closure** problem, also known as **project
selection**. The obvious readings all give the wrong number:

- **sum every positive weight** overcounts, because a positive config can force
  in costly negative dependencies you cannot avoid;
- **take every config** drags in avoidable negatives;
- **strongly-connected-component / reachability** reasoning (the shape of the
  previous version of this task) answers a different question entirely.

The exact optimum needs a non-obvious reduction to a **min s-t cut / max-flow**:
add a super source `s -> v` (capacity `w`) for each positive config, `v -> t`
(capacity `-w`) for each negative config, and `u -> v` (capacity infinity) for
each dependency edge; then the answer is `sum(positive weights) - maxflow(s, t)`.
The agent must recognise this reduction and implement max-flow from scratch (no
`networkx`/`scipy`/`igraph`), which is where trials diverge.

## Held out cases (measured)

Ground truth is recomputed independently in the verifier with a **different**
max-flow implementation (BFS Edmonds-Karp) than the oracle (Dinic). Answers below
are the verified oracle == reference values; the two small ones are also confirmed
by exhaustive brute force over all dependency-closed subsets.

| File | thr | offset | nodes | answer | what it exercises |
|------|-----|--------|-------|--------|-------------------|
| heldout_1 | 0 | 64 | ~9 | **220** | worth-it vs not-worth-it gadgets + a 3-node forced chain |
| heldout_2 | 0 | 96 | ~7 | **220** | a net-negative dependency **cycle** that only pays off when a high-value config pulls it in |
| heldout_3 | 0 | 96 | ~1400 | **35376** | scale: hundreds of mixed gadgets + free positives |
| heldout_4 | 150 | 64 | ~3 | **150** | optimum sits **exactly at the threshold** floor |
| heldout_5 | 0 | 96 | ~6 | **0** | every positive depends on a strictly costlier config, so the optimum is to activate nothing |

Each obvious-but-wrong strategy is off by a wide margin (verified by the bundled
harness against the reference):

| Wrong strategy | heldout_1 | heldout_3 | heldout_5 |
|----------------|-----------|-----------|-----------|
| correct answer | 220 | 35376 | 0 |
| sum all positive weights | 390 | 66165 | 180 |
| take every config | 180 | 16375 | 0 |

## Completion Rates

| Model | Agent | Pass rate |
|-------|-------|-----------|
| Oracle | `oracle` | 1.0 (deterministic; all 7 verifier tests pass) |
| Frontier models | `metacode` / `claude-code` | to be measured by the validation pipeline |

> **Calibration target:** unlike the previous version (a fully specified
> strongly-connected-component computation, which strong models implement
> correctly every time), this version hides a real insight barrier: the max-weight
> closure / min-cut reduction. Trials that reach for "sum the positives", "take
> everything", or SCC/reachability fail on every non-trivial held out, and trials
> that recognise the reduction still have to implement max-flow from scratch
> without a graph library. That is where the pass/fail split comes from.

## Anti Cheating

- **Hardcoded outputs:** the five held outs have different answers (220, 220,
  35376, 150, 0), thresholds (0, 150), offsets (64, 96) and sizes; all differ
  from the visible sample (110). A constant cannot satisfy them.
- **Overfitting to visible tests:** the only data in the container is the sample
  file; held outs live under `tests/` and are absent during the agent run.
- **Modifying test files:** tests and data are copied in only at verify time; the
  reward is computed by the verifier with an independent max-flow implementation
  (BFS Edmonds-Karp) different from the oracle's (Dinic), so it never trusts a
  value baked into the agent's script. `tests/_gen.py` (the deterministic
  generator) is co-located with the tests and never ships in the agent container.
- **Bypassing the intended path:** `test_from_scratch()` rejects numpy, scipy,
  networkx, igraph, pandas (which ship graph / max-flow routines) and shelling
  out (`subprocess`, `os.system`, `os.popen`, `__import__`, `importlib`, `eval`,
  `exec`), forcing a hand-written parser and max-flow.

Inspired by https://github.com/codimango/mehag-tbench/tree/main/mri-volume-calc
and https://github.com/codimango/purple29th-tbench-2/tree/main/android-depth-object-volume.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
