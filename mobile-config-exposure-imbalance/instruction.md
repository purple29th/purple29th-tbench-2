hey so i am in android mobile config lab we dump config dependency files off device in custom binary. each config has signed exposure weight, positive adds exposure negative costs it. you choose which configs to turn on but rule if you turn on a config you must also turn on everything it depends on transitively, otherwise rollout invalid. empty rollout is valid with total 0 and size 0.

your job is write script to /app/solve.py that reads file path from first arg and prints one number as last token. we run like python3 /app/solve.py /app/data/scene.mcfg, sample file at /app/data/scene.mcfg you can test locally. hidden grading uses other mcfg files you never saw with different sizes dependency chains exposure values thresholds. dont hardcode sample.

goal is two steps, this is exposure imbalance task so careful:
first find largest total exposure any valid rollout can reach, call it max exposure.
then among ALL valid rollouts that reach exactly that max exposure, find smallest number of configs turned on but with custom counting rule — header int32 reserved at offset 16 is exposure imbalance threshold, configs with abs(value) < threshold are free riders, they must be on if dependencies require but NOT counted in size. for example file with threshold 6, config value 5 with dep dangling is free rider, not counted even if reachable. this custom rule is why just counting reachable overcounts.

watch out traps i tried:
just adding up every positive is wrong because positive can drag in negative dependencies you cannot avoid.
turning on everything is also wrong because it pulls in avoidable costs.
some configs depend on each other in cycle so they must be activated as all or nothing, so singletons count as group of one, selection by total value not node count.
a dependency id that names no config in file is dangling and ignored, imposes no constraint.
zero-gain padding must be excluded, for example config +30 that depends on -30 does not change total exposure, so it can be included without changing max, but minimal rollout must leave such pairs out via residual graph.

binary format little endian, all ints:
first four bytes ascii M C F G magic at offset zero
next four bytes u32 version at four
next four bytes u32 node count at eight
next four bytes u32 data offset at twelve
next four bytes int32 reserved at sixteen — this is threshold now, not ignored, configs with abs(value) < threshold not counted in size, header is at least 64 bytes and data_offset may be larger than 64 with zero padding, so respect data_offset dont hardcode 64
then node_count records: each has signed int32 id, signed int32 value (signed exposure delta), unsigned uint32 dependency count, then that many unsigned uint32 dependency ids. all little endian. ids can be any int32 even negative, dep ids are uint32 and may name no node thats dangling.

parse it yourself from raw bytes with struct, no numpy scipy networkx igraph pandas or other graph array max flow libs. no shelling out via subprocess os.system os.popen importlib eval exec. use only stdlib. files may have up to about two thousand nodes, long chains will cause RecursionError if you use recursive dfs, so use iterative.

run as python3 /app/solve.py <path to mcfg> and print final number as last token on stdout.

grading exact int match on held-outs, we recompute ground truth independently with different max flow impl edmonds-karp vs dinic plus threshold counting, so hardcoded constant fails.
