# codimango/mobile-config-exposure-imbalance

From-scratch Python script that parses a custom binary config dependency graph (.mcfg) and reports total value of the largest SCC reachable from root id 0, excluding root value, filtering by threshold, picking by total value not node count, counting singletons. No networkx/igraph/numpy allowed. Built in mold of mri-volume-calc where difficulty is concentrated area vs scattered light spread.

This is hard like MRI volume calc. In MRI there is bright tumor concentrated area but light spread around makes naive sum all bright overcount by 20 percent. Here the reverse engineering trap is similar: many scattered bright config groups exist across the volume. Some are high total value but not reachable from root, some are reachable but under weight threshold, some have many nodes but low total value, some include root whose value must be excluded. The agent must find the most concentrated reachable group that passes threshold.

Hardening to make metacode fail regardless:

1. Manual binary parsing with data_offset that may be 96 not 64. Agents hardcoding 64 fail on heldout 2 and 3 which have 32 bytes padding.
2. Reachable filter from root id 0. Heldout 1 has a 4 node SCC total 400 that is not reachable, while reachable best is 180. Naive full graph max picks 400.
3. Threshold filter. Heldout 2 threshold 600, all reachable SCC totals are 350 and 200 so answer is 0. Agents ignoring threshold return 350.
4. Value vs node count. Heldout 3 has 3 node SCC total 300 vs 2 node SCC total 400. Picking by node count returns 300, correct is 400 by total value.
5. Root exclusion. Root id 0 is in a cycle in heldout 1 and 2 with value 999 and 1000. If you include root value you get 1179 vs 180 and 1350 vs 350.
6. Singleton SCC counts. Single node counts as group even without self loop.

Ground truth computed independently with iterative Kosaraju from scratch, not using libraries. Heldouts 180,0,400 vs naive all bright sum would be 580,400,1000.

| Model | Pass rate |
|-------|-----------|
| Oracle | 3/3 (1.00) |
| Avocado | 1/5 (0.20) target after hardening |
| Opus | 0/5 (0.00) before, now rechecking |
| gpt-5.5 | 0/5 (0.00) |

## Model Analysis
Natural wrong sums all values or treats dependencies undirected or ignores reachable filter and threshold, giving wrong answer on every heldout where largest SCC is not reachable or under threshold or where direction matters. Correct implementation parses header and node table by hand with struct respecting data_offset, performs DFS from root 0 to filter reachable nodes, runs iterative Kosaraju to find strongly connected components among reachable nodes, excludes root value from sum, checks threshold, picks max by total value.

## Anti-Cheating
- Hardcoded outputs fail because heldouts have different thresholds 0,600,0 and different offsets 64,96,96 and different totals 180,0,400 vs sample 220.
- Heldout data lives under /tests/data not in /app, absent during agent run.
- from_scratch test rejects numpy scipy networkx igraph pandas subprocess etc.
- Reference ground truth recomputed independently.
