We dump a config dependency file off an Android device in a custom binary format. Write your script to /app/solve.py that reads the file path from the first argument and prints one number.

Each config has a signed exposure weight. Positive adds exposure, negative costs it. You choose which configs to activate, but rule: if you activate a config you must also activate every config it depends on, transitively. A set respecting this is a valid rollout. Empty rollout is valid with total 0 and size 0.

Goal: first find the largest total exposure any valid rollout can reach. Then among all valid rollouts that reach that max, print the smallest number of configs turned on — the minimal rollout size. Do NOT print the exposure weight itself; printing the weight is wrong and will fail the held-out tests. Zero-gain padding must be excluded: for example a config +30 that depends on -30 does not change total exposure, so it can be included without changing max, but the minimal rollout must leave such pairs out. The correct minimal set is the configs reachable from source in the residual graph after max flow.

Watch out: just adding up every positive is wrong, because a positive can drag in negative dependencies you cannot avoid. Turning on everything is also wrong because it pulls in avoidable costs. Some configs depend on each other in a cycle, so they must be activated as all or nothing. A dependency id that names no config in the file is dangling and ignored.

Binary format. Little endian. Magic MCFG at offset zero. Version uint32 at four. Node count uint32 at eight. Data offset uint32 at twelve. Reserved int32 at sixteen — ignore it for this task, header is at least 64 bytes and data_offset may be larger than 64 with zero padding, so respect data_offset and do not hardcode 64. Then node_count records: each has signed int32 id, signed int32 value, unsigned uint32 dependency count, then that many unsigned uint32 dependency ids. All little endian. Sample file is at /app/data/scene.mcfg.

Parse it yourself from raw bytes with struct. No numpy, scipy, networkx, igraph, pandas or other graph, array or max flow libraries. No shelling out via subprocess, os.system, os.popen, importlib, eval or exec. Use only the standard library. Files may have up to about two thousand nodes.

Run as python3 /app/solve.py <path to mcfg file> and print the final number as the last token on stdout.
