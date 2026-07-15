# codimango/android-coroutine-scope-cancellation

From-scratch Python script that parses a custom binary config dependency graph, walks reachable nodes stopping at supervisor boundaries, and reports total weight. No networkx/igraph/numpy allowed. Graded on held-out files.

| Model | Pass rate |
|-------|-----------|
| Oracle | 3/3 |
| Avocado | measured on submission |
| Opus | measured on submission |

## Model Analysis
The natural approach sums the weight of every node reachable from the fail node, ignoring node type. That over-counts because supervisor nodes block cancellation propagation to their descendants in this model. The correct implementation parses the binary header and node table by hand with struct, walks the graph from the fail node, stops descending at supervisor nodes, and sums only the visited weights. The held-out files are constructed so the naive full-subtree sum differs substantially from the supervisor-pruned sum on every graded input.


<!-- revalidate b825dcc -->
