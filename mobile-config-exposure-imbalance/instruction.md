We dump a config dependency file off the device and it has this little binary format. Write your script to /app/solve.py that reads the file path from the first argument and prints one number.

Your goal is to find the total value of the group of configs that all mutually depend on each other and are reachable from the root config id zero. This is a strongly connected component SCC. Think of it like MRI tumor volume where there are many scattered bright groups across the volume like specks and noise. Some have high total but not reachable from root. Some are reachable but under threshold. Some have many nodes but low total. The concentrated area you need is the largest total value SCC that is reachable and passes threshold.

Rules for grading:

1. Single nodes count as groups even without a self loop. A singleton SCC is valid.
2. Pick by total value not by node count. Example two node group 200 plus 200 equals 400 beats three node group 100 each equals 300.
3. Root itself is just an entry point. Its own value is not counted. Only other configs in the group count. If root is part of a cycle its value must be excluded.
4. There is a minimum weight threshold in header. Only groups whose total meets threshold count toward answer. If no reachable group meets threshold answer is zero.
5. Reachability: only nodes reachable from root id zero via directed edges count. Groups not reachable must be ignored even if they have larger total.
6. Data offset in header may be larger than 64 with padding between header and records. You must respect data_offset field and not hardcode 64. Start reading records at data_offset.

Binary format details:

File is little endian with magic MCFG at offset zero. Version uint32 at four. Count uint32 at eight. Data offset uint32 at twelve. Weight threshold uint32 at sixteen. Header is at least 64 bytes. Then count records each with signed id int32, signed value int32, unsigned dependency count uint32, then that many unsigned dependency ids uint32. All little endian. A sample is in data folder as scene.mcfg.

Parsing constraints:

Parse it yourself from raw bytes with struct. No numpy, scipy, networkx, igraph, pandas or other graph or array libs. No shelling out via subprocess, os system, os popen, importlib, eval, exec. Use only standard library. Use iterative stack not recursion because graphs can be up to 100 nodes and recursion may hit limit.

We grade on files you have not seen with different thresholds and different offsets including zero threshold and high threshold cases.

Run as python3 /app/solve.py <path to mcfg file>
