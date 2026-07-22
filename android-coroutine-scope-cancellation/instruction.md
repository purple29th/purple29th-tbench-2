We dump a little graph off the device and need the weight of the cancelled cluster. Write your script to /app/solve.py that reads the file path from the first argument and prints one number, the total weight of nodes that get cancelled after a failure. Think of it like MRI tumor volume: there is a concentrated area that must be found precisely, but light spread around causes overcounting. Here naive sum of all nodes reachable from fail overcounts because supervisor nodes block spread like scattered noise, and you must find the precise cancelled cluster.

File is little endian with magic CSG1 at zero, version uint32 at four, node count uint32 at eight, edge count uint32 at twelve, root id uint32 at sixteen, fail node id uint32 at twenty, header total 64 bytes with padding after twenty. Then node count records of sixteen bytes each: int32 id, uint8 type zero normal one supervisor, int32 weight, seven bytes padding. Then edge count records of eight bytes each: int32 parent then int32 child. The graph can have cycles and diamond dependencies where a child has multiple parents.

Cancellation semantics precise and required for grading:
- Start with stack containing fail node.
- Maintain visited set to avoid infinite loops and double counting.
- Pop node, if already visited skip.
- Mark visited.
- If node exists in node table, add its weight to total even if it is a supervisor. Then if its type is supervisor equal one, do not enqueue its children, cancellation stops down that branch at supervisor boundary. If type is normal zero, enqueue all children.
- If node does not exist in node table but has children in edge table, still traverse children.
- If fail node itself is a supervisor, only its own weight counts, children are blocked.
- Diamond case: a node reachable via two parents, one parent path blocked by a supervisor and another unblocked, is still cancelled when reached via unblocked path because visited prevents double counting but unblocked path still counts. So cancellation is reachability via any unblocked supervisor chain.
- Root id is just info, not used for cancellation start, fail node is start.
- Graph may have cycles, use iterative stack to avoid recursion limit.

Sample file is in data folder as sample.sdb.

Parse it yourself with struct, no networkx, igraph, numpy, pandas or other graph or array libs, and no shelling out via subprocess os system popen importlib. We grade on files you have not seen including cases where fail node itself is a supervisor, where a cycle exists, and where a node is reachable via two parents one blocked by a supervisor and one not. Also files may have large size up to 100 nodes to test iterative not recursive.

Run as python3 /app/solve.py <path to sdb file>
