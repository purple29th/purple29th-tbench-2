We dump a config dependency file off the Android device and it has this custom binary format. Write your script to /app/solve.py that reads the file path from the first argument and prints one number.

Think of it like MRI tumor volume where there are many scattered bright groups across the volume like specks and noise and light spread around. The true tumor is the most concentrated bright area where pixels are mostly concentrated. Here many scattered config islands exist. Some have high total weight but are not reachable from the entry point. Some are reachable but under exposure threshold. Some have many nodes but low total weight. Some include the entry point whose weight must be excluded.

Goal: total weight of the most concentrated reachable mutual dependency island that passes exposure threshold.

Definitions:

A mutual dependency island is a set of config ids where every id can reach every other id following dependency edges. Single node counts as island even without self loop. This is the island where all configs all mutually depend on each other directly or indirectly.

Exposure threshold: header contains minimum total weight that an island must meet to count. If no reachable island meets threshold answer is zero.

Most concentrated: among islands that are reachable from root id zero and meet threshold, pick the one with largest total weight. If you pick by node count instead of total weight you will be wrong on some files. Example two node island with 200 plus 200 equals 400 beats three node island with 100 each equals 300.

Root exclusion: root id zero is just an entry point. Its own value is not counted toward total. Only other configs in the island count. Root can be part of a cycle. If root is in cycle you must exclude its value. Example cycle zero one two three where values are 999 plus 50 plus 60 plus 70 equals 1179 but answer excluding root is 180.

Reachability: only nodes reachable from root id zero via directed edges count. Islands not reachable must be ignored even if they have larger total. Example heldout with 200 node island total 15000 not reachable while reachable best is 10000.

Binary format:

File is little endian. Magic MCFG at offset zero. Version uint32 at four. Node count uint32 at eight. Data offset uint32 at twelve. Weight threshold uint32 at sixteen. Header is at least 64 bytes. Data offset may be larger than 64 with zero padding between header and records so you must respect data_offset field and not hardcode 64. Then node count records each with signed id int32, signed value int32, unsigned dependency count uint32, then that many unsigned dependency ids uint32. All little endian. Sample file is in data folder as scene dot mcfg with 6 nodes.

Parsing constraints:

Parse it yourself from raw bytes with struct. No numpy, scipy, networkx, igraph, pandas or other graph or array libs. No shelling out via subprocess, os system, os popen, importlib, eval, exec. Use only standard library. Use iterative stack not recursion because graphs can be up to about two thousand nodes and recursion will hit limit and dense graphs may need efficient walk.

We grade on files you have not seen with different thresholds zero and six hundred and ten thousand, different offsets 64 and 96, different sizes 6 to 2000 nodes, different traps like unreachable large islands, threshold zero fallback, root in cycle, value versus count.

Run as python3 /app/solve.py <path to mcfg file> and print final number as last token on stdout.
