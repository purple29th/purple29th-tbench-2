Hey, we've got a config dependency file dumped off an Android device and I need the total weight of the cancelled cluster. Write /app/solve.py that takes a path to a .sdb file and prints one number.

The .sdb format is little-endian with a 64-byte header: 4-byte magic "CSG1", uint32 version at 4, uint32 node_count at 8, uint32 edge_count at 12, uint32 root_id at 16, uint32 fail_node_id at 20. Then node_count records of 16 bytes each: int32 id, uint8 type 0 normal 1 supervisor, int32 weight, 7 bytes padding. Then edge_count records of 8 bytes each: int32 parent then int32 child. A supervisor node changes how cancellation spreads down that branch. There's a sample at /app/data/sample.sdb.

Parse it yourself with struct, no networkx, igraph, numpy, pandas or other graph or array libs, and no shelling out. We grade on files you haven't seen.
