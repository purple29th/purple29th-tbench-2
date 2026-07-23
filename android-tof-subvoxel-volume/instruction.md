Your code goes in /app/solve.py.

We will run it like python3 /app/solve.py /path/to/scan.tvol and you need to print the object's volume in cubic millimetres. We parse the last number on stdout as your answer.

Sample you can test on is /app/data/scene.tvol but hidden tests use other scans so don't hardcode sizes or values.

Our ToF rig writes a tiny custom binary .tvol. It's all little endian.

First four bytes are ascii TVOL.
At offset 4: uint32 version.
At offset 8: uint32 dtype code - 2 is int16 voxels, 16 is float32 voxels.
At offset 12: three uint32 nx ny nz - dimensions.
At offset 24: three float32 sx sy sz - physical voxel size in mm along each axis.
At offset 36: uint32 data_offset - where the voxel array begins.

After that, nx*ny*nz voxels of the given dtype, x fastest. So (x,y,z) maps to linear idx = x + nx * (y + ny * z).

In the scan the object is a bright blob but edges are fuzzy because lens point spread smears energy around. A voxel fully inside sits near a flat high peak, a voxel cut by the surface is lower because it's only partly filled, and that value bleeds into neighbours due to blur. On top there's a flat background level plus a little per-voxel noise. A few scans have one or two tiny isolated bright specks far from main blob - those are artefacts, drop them by keeping the biggest connected bright region. sx sy sz are anisotropic and vary file to file, so read them from header.

Parse it from raw bytes yourself. Only stdlib. No numpy, no scipy, no scikit-image, no opencv, no pillow, no networkx, no igraph, no imageio, no pandas, no torch, no tensorflow, no array / image / graph library at all. Also no subprocess, no os.system, no os.popen, no os.exec, no __import__, no importlib, no runpy, no ctypes, no eval, no exec, no compile, no shelling out.

At the end print volume in mm^3 as last token.
