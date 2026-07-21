Write a from-scratch Python script to /app/solve.py that reads a binary config dependency file, computes strongly connected components of the dependency graph, and prints one integer: the total value of the highest value SCC that is reachable from the root config, id zero.

The script reads the file path from its first command line argument.

Print exactly one integer to stdout: the sum of node values in the SCC with the greatest total value, restricted to SCCs reachable from root id zero. A single node with no mutual dependency is its own SCC size one. Select the winning SCC by total value, not by node count. The root node id zero is only an entry point, its own value is not included in any total.

Binary format, all integers little endian:
Offset four bytes type field
zero   four   bytes  magic equals MCFG
four   four   uint32 version
eight  four   uint32 record count
twelve four   uint32 data offset byte offset where records begin

At data offset, there are count records laid out contiguously. Each record:
four   int32  id signed
four   int32  value signed
four   uint32 dependency count D
four times D uint32 D dependency ids each an unsigned id

Each dependency id is a directed edge FROM this record TO that id.

Constraints: parse the format yourself with struct. Do not use numpy, scipy, networkx, igraph, pandas, or any other graph or array library. Do not shell out, no subprocess, os dot system, os dot popen, and do not use dynamic import eval exec compile importlib or ctypes. A sample file is at app data scene dot mcfg for local testing. Your script is graded on held out files you have not seen.
