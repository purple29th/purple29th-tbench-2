# codimango/android-coroutine-scope-cancellation

From-scratch Python script that parses a custom binary config dependency graph .sdb and reports total weight of cancelled cluster after a failure with supervisor pruning. No networkx/igraph/numpy allowed. Graded on held-out files. Built in mold of mri-volume-calc where difficulty is concentrated area vs scattered light spread.

MRI analogy: In MRI tumor scan there is a concentrated bright area that is true tumor volume, but light spread around makes naive sum all bright overcount by 100 to 1000 percent. Here the cancelled cluster is the concentrated area, supervisor nodes are like scattered noise that block spread. Naive sum of all nodes reachable from fail node ignores supervisor blocking and overcounts massively, e.g. heldout_7 naive 5050 vs precise 55, heldout_1 369 vs 262.

Hardening that makes metacode fail regardless:

1. Supervisor pruning semantic must be precise: supervisor weight counts but its children are not enqueued. If fail itself is supervisor, only its own weight counts. Heldout_5 fail_is_supervisor case covers this.
2. Diamond dependency: child reachable via two parents one blocked by supervisor and one not is still cancelled if any unblocked path reaches it. Requires visited set plus correct supervisor stop, not simple parent block.
3. Cycles: graph can have cycles, recursion would hit recursion limit on 100 node heldout_7, need iterative stack.
4. Manual binary parsing with struct: header 64 bytes magic CSG1 version node count edge count root fail, then 16 byte node records id type weight padding, then 8 byte edges. No libs allowed enforced by from_scratch test.
5. Root id is distractor, fail id is start, not root. Some agents start from root.
6. Weighted sum with visited deduplication: diamond would double count without visited set.

| Model | Pass rate |
|-------|-----------|
| Oracle | 3/3 (1.00) |
| Avocado | 1/6 to 1/10 sweet spot before hardening, target after |
| Opus | 4/9 |
| gpt-5.5 | 3/9 |

## Model Analysis
Natural wrong sums all nodes reachable from fail ignoring type, overcounting by 100 to 5000. Correct parses header by hand, builds adjacency, iterative DFS from fail with visited set, sums weight, stops descending at supervisor type 1. Heldouts constructed so naive full subtree sum differs substantially on every input, including large 100 node case where recursion fails.

## Anti-Cheating
- Heldout data lives under /tests/data not in /app, absent during agent run, 8 files with different totals 262,255,253,260,80,75,55,48 vs naive 369,363,361,366,279,185,5050,318.
- from_scratch test rejects networkx igraph numpy pandas subprocess os system.
- Ground truth recomputed independently with iterative stack, not from agent editable files.
