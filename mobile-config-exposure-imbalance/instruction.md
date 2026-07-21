We dump a config dependency file off the device and it has this little binary format. Write a python script that reads the file path from the first argument and prints one number, the total value of the biggest group of configs that all mutually depend on each other and are reachable from the root config, id zero.

The file is little endian with magic MCFG, version at four, count at eight, data offset at twelve, then count records each with id, value, dependency count, then that many dependency ids. A sample is in the data folder as scene dot mcfg.

Parse it yourself, no numpy, scipy, networkx, igraph or other graph or array libs, and no shelling out. We grade on files you have not seen.
