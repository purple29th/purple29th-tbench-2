Make a script at /app/solve.py. When we run:

python3 /app/solve.py /some/file.tvol

it should print a single float — the physical size of the thing inside the scan in cubic mm — and that number has to be the last thing on stdout.

You can try it locally on /app/data/scene.tvol, but final grading uses other scans you haven't seen, so it has to be generic.

What is .tvol? It's our own tiny ToF volume. Everything is little endian.

Bytes 0-3: ascii "TVOL"
Byte 4: uint32 version
Byte 8: uint32 dtype — 2 means int16, 16 means float32
Byte 12: uint32 nx, uint32 ny, uint32 nz (dimensions)
Byte 24: float32 sx, float32 sy, float32 sz — mm per voxel
Byte 36: uint32 data_offset — where voxels start

After data_offset there are nx*ny*nz voxels in that dtype, x is fastest. So linear index for (x,y,z) is x + nx*(y + ny*z).

Inside: the object looks like a bright blob with fuzzy edges. The sensor reports occupancy scaled — voxels deep inside are at a high flat peak, voxels cut by the surface are weaker, and the lens smears signal into neighbors due to point spread. On top there's a constant background plus a bit of noise in every voxel. Some scans have one or two very small bright specks far from the main blob; those are artefacts, don't count them. sx sy sz are different per axis and per scan, always read them.

You must parse raw bytes yourself, stdlib only. No array / image / graph helpers at all. That includes numpy, scipy, scikit-image, opencv, pillow, networkx, igraph, imageio, pandas, torch, tensorflow, etc. Also no shelling out, no subprocess, no os.system, no os.popen, no os.exec, and no trick imports — no __import__, no importlib, no runpy, no ctypes, no eval, no exec, no compile.

Output: print the object volume in mm^3; we take the last numeric token on stdout as your answer.
