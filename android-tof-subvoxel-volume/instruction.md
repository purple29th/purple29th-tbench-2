hey — this is from our ToF rig in the lab. we need a tiny solver script that lives at /app/solve.py.

how to run: python3 /app/solve.py <path to .tvol file>
what to output: the object's volume in cubic mm. we look at the last number you print, so make sure volume is last.

for dev you can use /app/data/scene.tvol — that's the only scan in the container. grading uses other .tvol files you haven't seen, so don't hardcode anything about size, spacing, or amplitude.

format: we made up .tvol, it's all LE. first 4 bytes are literally TVOL. then at offset 4 a uint32 version. at offset 8 a uint32 dtype — 2 means voxels stored as int16, 16 means float32. at offset 12 three uint32 nx ny nz — dims. at offset 24 three float32 sx sy sz — each voxel's physical size in mm. at offset 36 a uint32 data_offset — bytes where voxel array starts (don't hardcode 64).

then after data_offset, nx*ny*nz voxel values in that dtype, x changes fastest, so (x,y,z) -> x + nx*(y + ny*z).

what's inside: we put an object that shows up bright but with soft edges because optics have a PSF, wide sideways narrow in z. because of that a voxel fully inside is near a flat high plateau, a voxel cut by surface is lower (partial volume), and that signal bleeds into neighbours. on top of all voxels there's flat background plus small noise. some scans also have 1-3 tiny isolated bright dots far away from main object — those are specks / artefacts, you must ignore them by taking the biggest connected bright mass, not everything bright.

also sx sy sz are anisotropic and change per scan, so you have to read them, can't assume 1mm.

rules: you have to parse bytes yourself. only python stdlib allowed. no numpy, no scipy, no skimage, no cv2, no PIL, no networkx, no igraph, no imageio, no pandas, no torch/tensorflow — basically no array / imaging / graph helper. also no shell tricks — no subprocess, no os.system, no os.popen, no os.exec, no __import__, no importlib, no runpy, no ctypes, no eval/exec/compile.

final step: print the volume in mm^3, last token on stdout.
