I work on a PV line inspecting monocrystalline wafers after cell stringing. When a wafer has a microcrack, that region is electrically dead and shows up dark in electroluminescence (EL). We photograph the wafer with a cooled Si CCD.

EL lies though. Injected carriers diffuse laterally before radiative recombination, and the lens has a small point spread. The combo keeps total dark deficit the same but smears it outward into a wide gray halo. So a hairline crack that is truly 1.2 mm² looks like a big fuzzy cloud of 2.5 mm². Buyers care about true dead area in mm², not the cloud.

You have to write the measuring tool.

Save it at /app/solve.py. It will be run as python /app/solve.py <scan_path> . The last whitespace token printed on stdout is taken as the area.

We give you one wafer to develop on at /app/data/scene.elcr . You may open it locally. Hidden grading uses completely different wafers that differ in image size, pixel pitch, crack shape, EL brightness, background luminescence, diffusion length, and noise. Files are passed as random temporary paths. Do not hardcode numbers or absolute paths from the example file. Hardcoding the example area makes hidden checks fail.

What .elcr contains – custom binary for EL crack area, all little-endian:

- 0-3: ASCII magic ELCR
- 4-7: uint32 version
- 8-11: uint32 dtype tag: 2 means int16 pixels, 16 means float32 pixels
- 12-19: two uint32 dimensions nx, ny (pixels along x,y)
- 20-27: two float32 scales sx, sy in mm per pixel (anisotropic and file dependent, you must read them)
- 28-31: uint32 offset where pixel block starts
- from offset onward: nx*ny samples in declared dtype, x moves fastest, linear index is x + nx * y. Dark crack was already inverted to bright during export so the defect appears bright on top of flat background.

What is inside:
One principal microcrack network (the one we grade) plus occasionally one or two isolated tiny bright spots far away due to dust or chamfer chipping. Those spots must not be counted. Keep only the main connected structure using 8-neighbour connectivity and pick the component with largest integrated excess signal, not largest pixel count – dust can cover more pixels but carry less total dark deficit, and can be brighter per pixel than the main crack.

Why just counting bright pixels fails:
A generous brightness cutoff pulls in the wide carrier-diffusion halo and roughly doubles the area, sometimes more. A strict cutoff keeps only the very brightest core and loses the thin branching arms that never become fully bright because of partial coverage – that halves the area. No single level works across wafers because camera gain, wafer luminescence, diffusion length and background all shift batch to batch. What is conserved is total signal, not how many pixels are over a level.

The difficulty is a small pipeline: first estimate background wafer luminescence without bias from the crack, then estimate noise floor, then separate main crack energy from far specks, then estimate the true interior defect level that would be seen without diffusion and without being fooled by read noise spikes, then grow outward to capture the faint halo that belongs to the crack until the halo's mean excess falls into noise, but stop before you bridge to a distant speck. Missing halo under-counts because much energy lives there when diffusion is wide; including specks over-counts.

We grade at 3% relative error. Simple level counting is far outside.

Coding rules – your solve.py is scanned by AST plus runtime audit hook:
- Parse binary yourself. Allowed imports only: struct, sys, math, random, tempfile, re.
- Forbidden libraries and will fail test_from_scratch: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, os, io, posixpath, ntpath, genericpath, plus any other array, imaging, or graph helper.
- Forbidden calls: eval, exec, compile, __import__, chr
- Forbidden runtime: subprocess, os.system, os.popen, os.exec, os.fork, os.walk, os.listdir, os.scandir, os.open, pty, importlib, runpy, ctypes, any directory listing, plus tricks hiding paths via chr, bytes.fromhex, base64, b64decode, bytearray, bytes([...]) or string concatenation building forbidden locations.
- Do not try to open or list /tests and do not mention test_outputs, heldout, reference_volume, _gen, GEOM_TRUTH, geometric_truth in solve.py.
- Must work on any temporary file path, not a fixed path.

Print the dead area in mm2 as the last token. Example line: 12.345
