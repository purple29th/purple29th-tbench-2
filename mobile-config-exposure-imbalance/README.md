# codimango/mobile-config-exposure-imbalance

## Description

Agent writes stdlib only Python at /app/solve.py that reads custom MCFG binary with signed exposure deltas and dependencies where abs below threshold are free riders not counted and their own dependencies ignored, changing closure graph itself. Find max total exposure per transitive rules, then minimal counted size among optimal rollouts excluding free riders and zero gain padding, ignoring dangling, handling up to 3500 node chains that break recursion.

Watch out: summing positives wrong, turning on everything wrong, cycles all or nothing, dangling ignored, data_offset 96/128 padding respect header not hardcode 64, threshold at offset 16 is exposure imbalance threshold configs with abs below threshold not counted and their own deps ignored, long chain 3500 nodes forces iterative stack not recursive DFS. Chain is 3500.

Format: magic MCFG version count offset threshold header at least 64, then nodes int32 id int32 value uint32 dep count then that many uint32 dep ids little endian negative stored as two complement.

Implement max closure via min cut then minimal via residual reachable capacity >0 counting only abs >= thr.

## Measured difficulty

Max closure via min cut plus residual minimal plus threshold counting with free rider dep ignore passes. Summing positives fails, turning on everything fails, counting reachable without residual capacity check fails overcounts 22 vs 1 for chain 3500.

7 heldouts have answers 5,1,683,3,4,1,4,415 and 8 heldouts now? Actually 8 have 5,1,683,3,4,1,4,415 all different from sample 3 so constant fails.

## Completion Rates

Oracle 3/3 100 percent deterministic Dinic iterative plus residual handles 3500 chain, Avocado expected 2 to 3/5 fails expected due to recursive DFS fails on 3500 chain and padded overcounts and threshold without dep ignore, Opus 4/5 expected 1 timeout on large random 683 nodes, GPT 5/5 expected strong closure solver.

## Model Analysis

Dominant failures: recursive DFS stack overflow on 3500 chain, missing signed dep handling for negative IDs stored as uint32, including zero gain padding, counting free riders abs below thr, not respecting data_offset padding.

## Anti-Cheating

Hardcoded fails: 8 heldouts have different answers 5,1,683,3,4,1,4,415 vs sample 3. Overfit blocked: only scene.mcfg at /app/data, hidden under /tests mounted only at verify, copied to neutral temp name and solve.py copied into isolated temp dir. Generator _gen.py not mounted. Reward hacking hardened: test_from_scratch uses AST for imports calls and decoded literals for path checks not raw compact substring like pty dot that falsely matches empty dot, bans many modules via AST.

Author: Tosin Daniel Jimoh
