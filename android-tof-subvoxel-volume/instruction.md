write a script at /app/solve.py — that's where we run it.

usage: python3 /app/solve.py <path to .tvol file>

it should output the object's volume in mm^3. last number on stdout is graded.

local sample is at /app/data/scene.tvol for dev, hidden tests use other scans so don't hardcode.

format is ours, .tvol, little endian. starts with TVOL ascii at 0. at 4 bytes offset you get uint32 version. at 8 bytes dtype code uint32 — 2 means voxels are int16, 16 means float32. at 12 three uint32 nx ny nz. at 24 three float32 sx sy sz — that's mm per voxel per axis. at 36 uint32 data_offset — voxels start there.

then nx*ny*nz values of that dtype, x moves fastest, so (x,y,z) linear is x + nx*(y + ny*z).

what you see: main thing is bright blob but fuzzy because optics have point spread, interior near flat high, surface voxels weaker due to partial fill, and that leaks to neighbors. there's flat bg plus per-voxel noise. sometimes 1-2 tiny bright specks far from main — ignore them, keep only biggest bright region. sx sy sz differ per axis and per file, must read them.

impl: parse bytes yourself, stdlib only. no numpy, scipy, scikit-image, opencv, pillow, networkx, igraph, imageio, pandas, torch, tensorflow, or any array / imaging / graph helper. no shelling, no subprocess, no os.system/popen/exec, no __import__/importlib/runpy/ctypes/eval/exec/compile.

print volume mm^3 as last token.
