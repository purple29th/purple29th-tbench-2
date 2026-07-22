We dump a little graph off the device and need the weight of the cancelled cluster. Write your script to /app/solve.py that reads the file path from the first argument and prints one number, the total weight of nodes that get cancelled after a failure.

The file is little endian with magic CSG1, version at four, node count at eight, edge count at twelve, root id at sixteen, fail node id at twenty, then sixty four byte header total. Then node count records of sixteen bytes each: int32 id, uint8 type zero normal one supervisor, int32 weight, seven bytes padding. Then edge count records of eight bytes each: int32 parent then int32 child. Cancellation starts at the fail node and walks down children, but a supervisor node changes how cancellation spreads down that branch. A sample is in the data folder as sample dot sdb.

Parse it yourself with struct, no networkx, igraph, numpy, pandas or other graph or array libs, and no shelling out. We grade on files you have not seen.
