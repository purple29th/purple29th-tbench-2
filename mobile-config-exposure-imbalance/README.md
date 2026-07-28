# codimango/mobile-config-exposure-imbalance

## Description

Agent writes stdlib-only Python at /app/solve.py that reads custom MCFG binary with signed exposure deltas and dependencies where abs(value) < threshold are free riders not counted and their own dependencies ignored, changing closure graph itself. Find max total exposure per transitive dependency rules, then minimal counted size among optimal rollouts excluding free riders and zero gain padding, ignoring dangling deps, handling up to 3500 node chains that break recursion.

Watch out: summing positives wrong, turning on everything wrong, cycles all or nothing, dangling ignored, data_offset may be 96/128 with zero padding so respect header not hardcode 64, threshold at offset 16 is exposure imbalance threshold, configs with abs below threshold not counted and their own deps ignored, long chain 3500 nodes forces iterative stack not recursive DFS.

Format: first magic MCFG, version at 4, node count at 8, data offset at 12, int32 threshold at 16, header at least 64 bytes, then node records: signed int32 id, signed int32 value, uint32 dep count, then that many uint32 dep ids little endian, ids can be negative stored as uint32 two complement, dep may be dangling.

Implement max closure via min cut, then minimal via residual graph reachable with capacity >0, counting only abs >= thr.

## Measured difficulty

| Strategy | Result |
|----------|--------|
| Max closure via min cut plus residual minimal plus threshold counting with free rider dep ignore | passes |
| Summing all positives | fails, drags unavoidable negatives |
| Turning on everything | fails, pays avoidable costs |
| Counting reachable without residual capacity check | fails, includes zero gain padding overcounts 22 vs 1 for chain 3500 |

3 percent? Actually exact int match grading, 7 heldouts with answers 6,5,623,0,2,1,4 all different from sample 3 so constant fails.

## Completion Rates

| Model | Pass rate | Notes |
|-------|-----------|-------|
| Oracle | 3/3 100 percent | deterministic Dinic iterative plus residual, handles 3500 chain |
| Avocado 5.14 | 2 to 3/5 expected | recursive DFS fails on heldout_6 3500 chain RecursionError, padded rollout overcounts, threshold counting without dep ignore overcounts |
| Opus 4.8 | 4/5 expected | 1 timeout on large random 623 nodes |
| GPT 5.5 | 5/5 expected | strong closure solver |

## Model Analysis

Dominant failures: recursive DFS stack overflow on 3500 chain, missing signed dep handling for negative IDs stored as uint32, including zero gain padding, counting free riders with abs < thr, not respecting data_offset padding.

## Anti-Cheating

Hardcoded fails: 7 heldouts have different answers 6,5,623,0,2,1,4 vs sample 3. Overfit blocked: only scene.mcfg at /app/data, hidden under /tests mounted only at verify, copied to neutral temp name and solve.py copied into isolated temp dir. Generator _gen.py not mounted. Reward hacking hardened: test_from_scratch uses AST for imports calls and decoded literals for path checks, not raw compact substring like pty dot that falsely matches empty dot in comments, bans many modules via AST.

Author: Tosin Daniel Jimoh - Android mobile config exposure imbalance
