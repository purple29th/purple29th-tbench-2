We dump a config dependency file off an Android device in a custom binary format. Write your script to /app/solve.py that reads the file path from the first argument and prints one number.

Each config has a signed exposure weight. Positive means it adds exposure, negative means it costs exposure. You get to choose which configs to activate, but there is a rule: if you activate a config you must also activate every config it depends on, and every config those depend on, and so on. A set of configs that respects this rule is a valid activation set.

Goal: print the largest total exposure weight you can get from any valid activation set. You can always activate nothing, which gives zero, so the answer is never negative. If the best you can do is below the exposure threshold in the header, print 0.

Watch out: just adding up every positive config is wrong, because a positive config can drag in negative configs it depends on that you cannot avoid. Activating everything is also wrong, because it pulls in costs you did not need. Some configs depend on each other in a cycle, so they come as all or nothing. A dependency id that names no config in the file is ignored.

Binary format. Little endian. Magic MCFG at offset zero. Version uint32 at four. Node count uint32 at eight. Data offset uint32 at twelve. Weight threshold as a signed int32 at sixteen. Header is at least 64 bytes and data offset may be larger than 64 with zero padding, so respect the data_offset field and do not hardcode 64. Then node count records, each with a signed int32 id, a signed int32 value, an unsigned uint32 dependency count, then that many unsigned uint32 dependency ids. All little endian. A sample file is in the data folder as scene dot mcfg.

Parse it yourself from raw bytes with struct. No numpy, scipy, networkx, igraph, pandas or other graph, array or max flow libraries. No shelling out via subprocess, os system, os popen, importlib, eval or exec. Use only the standard library. Files may have up to about two thousand nodes.

Run as python3 /app/solve.py <path to mcfg file> and print the final number as the last token on stdout.
