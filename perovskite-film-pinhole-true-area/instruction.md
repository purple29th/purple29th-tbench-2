I QC perovskite solar films right after slot-die coating and annealing. A good film photoluminesces uniformly under 405 nm excitation. Where there is a pinhole – tiny region where perovskite didn't form and HTL is exposed – PL is quenched and that spot looks dark. We image PL with a sCMOS through a 750 nm long-pass.

PL imaging smears the truth. Photo-generated carriers travel a diffusion length before recombining, and the objective has a small Airy spread. Their combined effect conserves total quenched signal but pushes it outward into a fuzzy gray halo. A pinhole that is really 0.15 mm² looks like 0.32 mm² on camera. The line wants true dead area in mm² for shunt-risk grading, not the halo-inflated cloud.

You will write the measurement tool.

Put it at /app/solve.py . Grader runs python /app/solve.py <scan_path> and uses the last whitespace token on stdout as your answer.

For local dev we provide one film at /app/data/scene.ppha . You may open it. Hidden grading uses different films that vary in image size, pixel pitch, pinhole shape, PL brightness, film background, diffusion length, and camera noise. Those files come as random temporary paths. Do not hardcode numbers or absolute paths from the example. Hardcoding the example area fails hidden checks.

Format .ppha – custom binary for PL pinhole area, all little-endian:

- 0-3: ASCII magic PPHA
- 4-7: uint32 version
- 8-11: uint32 dtype: 2 = int16 pixels, 16 = float32 pixels
- 12-19: two uint32 nx, ny pixels along x,y
- 20-27: two float32 sx, sy mm per pixel (anisotropic, file dependent, you must read them)
- 28-31: uint32 offset to pixel data
- from offset: nx*ny values in declared dtype, x fastest, index = x + nx * y. Pinholes were inverted to bright during export so defect is bright over flat film background.

Inside each file:
One main pinhole cluster (the one we grade) plus at times one or two tiny isolated bright dots far away from coating dust or handling. Those must not be counted. Keep only the principal connected structure using 8-neighbour connectivity and choose component with largest integrated excess signal, not largest pixel count – dust can be larger in pixels but weaker in total quench, and can be brighter per pixel than main pinhole.

Why naive bright counting fails:
Counting everything above a generous level includes the diffusion halo and roughly doubles area, sometimes more. Counting only very bright core misses thin feathered arms where HTL is only partly exposed – those never become fully bright because of partial coverage – cutting area roughly in half. No global level works across films because PL gain, film background, diffusion length and noise shift lot to lot. What is preserved under blur is total integrated deficit, not count of pixels over a level.

The hard part is a small pipeline: first estimate film background without bias from pinhole, then noise floor, then isolate main pinhole energy from far specks, then estimate true interior quench level that would be seen without diffusion and without being tricked by read spikes, then grow outward to include faint halo belonging to pinhole until mean excess falls into noise, but stop before bridging to a distant speck. Missing halo under-counts because much energy lives there when diffusion is wide; adding specks over-counts.

Grading at 3% relative error. Simple thresholds are far outside.

Coding rules – solve.py is scanned by AST and runtime audit hook:
- Parse yourself. Allowed imports: struct, sys, math, random, tempfile, re.
- Forbidden and will fail test_from_scratch: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, os, io, posixpath, ntpath, genericpath, plus any other array/imaging/graph helper.
- Forbidden calls: eval, exec, compile, __import__, chr
- Forbidden runtime: subprocess, os.system, os.popen, os.exec, os.fork, os.walk, os.listdir, os.scandir, os.open, pty, importlib, runpy, ctypes, any directory listing, plus hiding paths via chr, bytes.fromhex, base64, b64decode, bytearray, bytes([...]) or concatenation building forbidden locations.
- Do not open/list /tests and do not mention test_outputs, heldout, reference_volume, _gen, GEOM_TRUTH, geometric_truth in solve.py.
- Must work on any temporary file path.

Print dead area mm2 as last token. Example: 0.1842
