# codimango/mobile-config-exposure-imbalance

## Description

Agent writes stdlib-only Python at `/app/solve.py` that parses a custom Android mobile config binary (`.mcfg` magic `MCFG`) dumped off device. Each config has signed exposure delta (positive adds exposure, negative costs), and turning a config on forces on every config it depends on transitively. Empty rollout valid with 0 exposure 0 size.

Goal is two-step exposure imbalance fix:
1. Find max total exposure any valid rollout can reach (max-weight closure / min-cut).
2. Among all rollouts reaching that max, print smallest number of configs turned on — minimal rollout size. Do NOT print exposure value; zero-gain padding (+30 depends on -30) must be excluded via residual graph reachability.

Watch out: summing positives wrong (drags unavoidable negatives), turning on everything wrong (pays avoidable costs), cycles must be all-or-nothing, dangling dep ids naming no config are ignored, data_offset may be 96/128 with zero padding so respect header not hardcode 64, reserved field ignored but header at least 64.

This is hardened version to fix previous Too Easy 5/5 and BAD_GRADING_WRONG:
- explicit `/app/solve.py` path now in instruction (fixes 9/12 test_exists fails)
- spec clarifies singletons count as group of one, selection by total value not node count, empty allowed, minimal not maximal
- long chain 2000 nodes forces iterative stack not recursive DFS (RecursionError)
- header offset 128 with padding tests robust parsing
- negative IDs, dangling IDs, zero-gain heavy (20 pads) to catch padded rollout

## Completion Rates (measured after hardening)

| Model | Agent | Pass rate | Notes |
|-------|-------|-----------|-------|
| Oracle | oracle | 3/3 (1.0) | deterministic Dinic + residual reachability, handles 2000-chain iterative |
| Avocado (expected) | metacode | 2-3/5 fails expected | recursive DFS fails on heldout_6 2000 chain -> RecursionError, padded rollout overcounts on heldout_5/6 |
| Sonnet/Opus (expected) | claude-code | 3-4/5 | should show split after hardening, previously 5/5 too easy |

Oracle verified 3/3 mean 1.0. After hardening, added heldout_6 (2000 chain) and heldout_7 (negative IDs + many dangling) to drop avocado from 5/5 to 2-3/5 expected.

## Model Analysis

- **Too Easy baseline**: previous version had only small graphs ~11 nodes, no chain, avocado could memorize Dinic and pass 5/5. Added chain 2000 nodes that breaks naive recursive DFS (Python recursion limit 1000) -> causes process crash before writing solve.py in some trials, also BFS Edmonds-Karp slow.
- **Zero-gain padding trap**: 20 zero-gain pads in heldout_6, 10 in heldout_5. Naive source-side count that includes zero-cap edges overcounts (22 vs 2). Only residual graph with capacity>0 exclusion gets minimal.
- **Empty best trap**: heldout_4 answer 0 where every positive depends on costlier negative. Summing positives gives >0 and fails.
- **Dangling deps trap**: dep ids like 4_000_000_000 name no node, must be ignored. If treated as node, graph includes phantom nodes and answer wrong.
- **Header offset trap**: offset 128 with zero padding, if hardcoded 64 then parses garbage.
- **Singleton vs cycle confusion** (old review e14085c): fixed by clarifying singletons count as group, selection by total value, minimal rollout not maximal.

## Anti-Cheating Analysis

- **Hardcoded rollout sizes blocked**: 7 heldouts have answers 6,5,650,0,2,? (chain ~1999?),? (dangling) all different from sample (sample answer 3). Sample at /app/data/scene.mcfg has answer 3 (configs 1,2,8). Constant or memorized fails.
- **Overfit to visible file blocked**: only scene.mcfg exists in agent container, its graph (100->-30 worth it, 50->-80 not worth it, 40 dangling free, 30->-30 zero-gain pad) differs from hidden graphs: cycle, large random 1400, empty, 10 pads, 2000 chain, negative IDs. Hidden dumps under /tests mounted only at verify.
- **Test file editing worthless**: heldouts + generator under tests/ invisible to agent during trajectory, mounted only at verify time. Reward computed independently via different max-flow impl (Edmonds-Karp BFS) vs oracle Dinic, so line-for-line reproduction not rewarded but both give same minimal size.
- **Library bypass blocked**: test_from_scratch() AST audits imports/calls, rejects numpy, scipy, skimage, cv2, PIL, networkx, igraph, imageio, pandas, torch, tensorflow, subprocess, importlib, etc., plus token scan blocks /tests, heldout, os.system, etc. Forces genuine struct parsing + hand-written iterative max-flow.

Author: Tosin Daniel Jimoh <purple29th@meta.com> - Android mobile config exposure imbalance, max-weight closure with minimal rollout hardening
