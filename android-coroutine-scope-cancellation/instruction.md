Hey, we've got a config dependency file dumped off an Android device and I need the total weight of the cancelled cluster. Write /app/solve.py that takes a path to a .csg file and prints one number, counting only configs reachable from the root config id 0 and stopping at supervisor boundaries.

The .csg format is little-endian with a 64-byte header: 4-byte magic "CSG1", uint32 version at 4, uint32 node_count at 8, uint32 edge_count at 12, uint32 root_id at 16, uint32 fail_node_id at 20. Then node_count records of 16 bytes each: int32 id, uint8 type 0 normal 1 supervisor, int32 weight, 7 bytes padding, sorted by id in the file. Then edge_count records of 8 bytes each: int32 parent then int32 child, a directed edge from parent to child. Sample at /app/data/sample.sdb.

Parse it yourself with struct, no networkx, igraph, numpy, pandas or other graph or array libs, and no shelling out. We grade on files you haven't seen.
