# codimango/mobile-config-exposure-imbalance

From scratch Python script that parses a custom Android mobile config binary MCFG and reports total weight of the most concentrated reachable mutual dependency island that passes exposure threshold. No graph libraries allowed. Built in mold of mri volume calc and android depth object volume where difficulty is concentrated area versus scattered light spread.

This is hard like MRI tumor scan. In MRI there is a bright tumor concentrated area but light spread around makes naive sum all bright overcount by twenty percent. Here reverse engineering trap is similar: many scattered config islands exist across the file. Some have high total weight but not reachable from root. Some are reachable but under weight threshold. Some have many nodes but low total weight. Some include root whose weight must be excluded. The agent must find the most concentrated reachable island that passes threshold, like finding tumor core while ignoring scattered pixel spread.

Hardening to make metacode fail regardless inspired by MRI precision:

1. Manual binary parsing with data offset that may be ninety six not sixty four. Agents hardcoding sixty four fail on heldout two and three which have padding.
2. Reachable filter from root id zero. Heldout one has a four node island total four hundred that is not reachable while reachable best is one hundred eighty. Naive full graph max picks four hundred.
3. Threshold filter. Heldout two threshold six hundred, all reachable island totals are three fifty and two hundred so answer is zero. Agents ignoring threshold return three fifty.
4. Value versus node count. Heldout three has three node island total three hundred versus two node island total four hundred. Picking by node count returns three hundred, correct is four hundred by total value.
5. Root exclusion. Root id zero is in a cycle in heldout one and two with value nine nine nine and one thousand. If you include root value you get eleven seventy nine versus one eighty and thirteen fifty versus three fifty.
6. Singleton islands count. Single node counts as group even without self loop.
7. Large graphs five hundred to two thousand nodes so recursion fails and inefficient all pairs fails, need iterative stack from scratch.

Ground truth computed independently with different traversal order than solution, using lowlink stack method versus first solution order, not using libraries. Heldouts one eighty, zero, four thousand versus naive all sum would be five eighty, nine hundred, twelve ten.

| Model | Pass rate |
|-------|-----------|
| Oracle | 3/3 |
| Avocado | target one of five after hardening, currently pending |
| Opus | pending |
| gpt 5.5 | pending |

## Model Analysis
Natural wrong sums all values or treats dependencies undirected or ignores reachable filter and threshold or includes root, giving wrong answer on every heldout where largest island is not reachable or under threshold or where direction matters or where root must be excluded. Correct implementation parses header and node table by hand with struct respecting data offset, performs iterative reachability from root zero to filter nodes, finds mutually dependent islands among reachable nodes with iterative depth first search that handles cycles and diamonds, excludes root value from sum, checks threshold, picks max by total value.

## Anti Cheating
- Hardcoded outputs fail because heldouts have different thresholds zero six hundred zero and different offsets sixty four ninety six ninety six and different totals one eighty zero four hundred versus sample two twenty and large sizes five hundred thousand versus sample six.
- Heldout data lives under tests data not in app, absent during agent run.
- From scratch test rejects numpy scipy networkx igraph pandas subprocess etc.
- Reference ground truth recomputed independently with alternative method.

Inspired by https://github.com/codimango/mehag-tbench/tree/main/mri-volume-calc and https://github.com/codimango/purple29th-tbench-2/tree/main/android-depth-object-volume where concentrated high intensity area versus spread pixel light makes precise volume hard. Here concentrated reachable island versus scattered unreachable and under threshold islands makes precise exposure hard.
