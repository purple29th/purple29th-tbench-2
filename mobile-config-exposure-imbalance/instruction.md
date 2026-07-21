Hey, quick one - we dump a config dependency file off the device and it has this little binary format. Can you write /app/solve.py that reads the file path from the first argument and prints one number: the total value of the biggest group of configs that all mutually depend on each other and are reachable from the root config, id 0.

The little-endian .mcfg is: magic "MCFG", uint32 version at 4, uint32 count at 8, uint32 data_offset at 12, then count records of {int32 id, int32 value, uint32 dep_count, then dep_count uint32 dependency ids}; a sample is at /app/data/scene.mcfg.

Parse it yourself, no numpy, scipy, networkx, igraph or other graph or array libs, and no shelling out. We grade on files you haven't seen.
