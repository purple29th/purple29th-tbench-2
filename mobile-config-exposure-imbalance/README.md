# codimango/mobile-config-exposure-imbalance

From-scratch Python script that parses a custom binary config dependency graph (.mcfg) and reports total value of the largest SCC reachable from root id 0. No networkx/igraph/numpy allowed. Graded on held-out files with independent ground truth.

| Model | Pass rate |
|-------|-----------|
| Oracle | 3/3 (1.00) |
| Avocado | 1/5 (0.20) |
| Opus | 0/5 (0.00) |
| gpt-5.5 | 0/5 (0.00) |

## Model Analysis
The natural approach sums all values or treats dependencies as undirected, giving a wrong answer on every held-out where the largest SCC is not reachable from root or where direction matters. Correct implementation parses header and node table by hand with struct, performs DFS from root 0 to filter reachable nodes, runs Kosaraju to find strongly connected components among reachable nodes, and sums the largest by value. Held-out files are constructed so naive full-graph sum differs substantially from the reachable-filtered sum.
