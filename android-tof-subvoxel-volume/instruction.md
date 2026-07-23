ok so we have this little ToF sensor rig in the lab — it's on a phone, we put a small object in front and it dumps a 3d volume. i need you to write the solver that lives at /app/solve.py. when we run python3 /app/solve.py <path to a .tvol file> it should print the object's volume in cubic mm. we take the last number on stdout.

you can develop using the sample scan that's at /app/data/scene.tvol. that's the only file in the container. final grading uses other .tvol files you haven't seen, with different sizes, spacings, brightness, and specks, so don't hardcode anything from the sample.

i made up a tiny binary format called .tvol, it's all little endian. layout is:

- first 4 bytes: ascii letters T V O L
- at byte offset 4: uint32 version
- at byte offset 8: uint32 dtype code. value 2 means voxels are int16, value 16 means float32
- at byte offset 12: three uint32s: nx, ny, nz. that's how many voxels on each axis
- at byte offset 24: three float32s: sx, sy, sz. that's physical size of one voxel in mm along x y z
- at byte offset 36: uint32 data_offset. that's byte where voxel data starts. don't hardcode 64, use data_offset, header may have padding.

then after data_offset: nx * ny * nz numbers of that dtype. x is fastest, then y, then z. so linear index for coordinate (x,y,z) is x + nx * (y + ny * z). i know it's a bit annoying but that's how we dump it.

what's in the data: we put a solid object, bright region. because of optics point spread, edges are not sharp, they're soft and fuzzy. the PSF is wider sideways than along z. so interior voxels are at a flat high plateau, voxels that are only partly covered by object surface are lower, partial volume effect, and that energy smears into neighbors due to blur. on top of that every voxel has a flat background level plus small noise. some scans also have one to three tiny isolated bright dots far away from main blob — those are sensor specks / artefacts, you must ignore them. easiest is to take largest connected bright region with 26 connectivity, that drops specks.

also note: you can't just threshold and count voxels. that fails because thin parts never reach threshold and halo from blur makes core too big. blur kernel is normalized so total intensity is conserved. correct approach (hinted in task description) is intensity conservation: estimate background, subtract, estimate interior plateau amplitude, integrate background-subtracted intensity over object plus its faint halo, divide by amplitude, multiply by sx*sy*sz.

you have to parse file from raw bytes yourself. only python stdlib. don't import numpy, scipy, scikit-image, opencv, pillow, networkx, igraph, imageio, pandas, torch, tensorflow, or any other array / imaging / graph library. also don't shell out: no subprocess, no os.system, no os.popen, no os.exec, no __import__, no importlib, no runpy, no ctypes, no socket, no multiprocessing, no glob, no eval/exec/compile.

at the end, print the volume in mm^3 as final token on stdout. we parse last number.

thanks!
