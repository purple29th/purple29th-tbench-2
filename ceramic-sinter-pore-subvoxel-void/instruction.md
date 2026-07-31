I run quality checks on ballistic ceramic tiles that were formed by spark-plasma sintering of silicon carbide powder. After densification there are often sealed internal pores left behind that become crack initiation points. We image tiles with a cone-beam lab micro-CT system at 90 kV.

The problem is the imaging itself lies. The X-ray source is not an ideal point, the detector has a scintillator spread, and there is Compton scatter inside the dense tile. The combined effect is a blur that keeps the total signal energy but pushes it outward into a wide fuzzy fringe. So on screen a pore that is actually compact looks like a huge glowing cloud. Customer wants the real geometric pore size in mm³, not the apparent cloud size.

You must write the tool that does this.

Save it as /app/solve.py. Grader runs python /app/solve.py <path_to_scan> and takes the final whitespace token from stdout as your answer.

We include one tile scan to develop with: /app/data/scene.cspv . You can open that while coding. The hidden evaluation set uses completely different scans that vary in grid shape, voxel pitch, ceramic bulk density, pore brightness, scatter width, background level, and noise. They are passed as randomly named temporary files. Do not embed numbers or absolute paths from the example file. Any solution that hardcodes the example volume fails the hidden checks.

File format – .cspv – small custom container, all little-endian:

- bytes 0-3: ASCII magic CSPV
- 4-7: uint32 version
- 8-11: uint32 data type tag: 2 = signed int16, 16 = float32
- 12-23: three uint32 dimensions: nx, ny, nz (voxels along x,y,z)
- 24-35: three float32 scale factors: sx, sy, sz in mm per voxel (anisotropic and file dependent – you must read it)
- 36-39: uint32 offset to start of voxel block
- from offset onward: nx*ny*nz samples in the declared type, x moves fastest, so linear address for (x,y,z) is x + nx * ( y + ny * z ). In the file the dark void was inverted during export so that pore voxels appear bright.

What is inside each file:
A single dominant sealed pore (the one we grade) plus sometimes one or two tiny isolated bright dots far away caused by un-sintered powder granules. Those dots must not be counted. To get rid of them keep only the principal connected structure using 26-neighbour volumetric connectivity and choose the component with the most integrated excess signal. The pore interior has a flat saturated plateau, edges are diluted by partial volume and then further smeared by the X-ray blur. The rest of the tile is a roughly flat matrix brightness plus detector noise.

Why naive voxel counting does not work here:
If you count everything above a generous brightness you absorb the diffuse halo that surrounds every pore and the result is roughly double the true physical size, sometimes more. If you count only very bright voxels you miss the thin fissure-like extensions from sintering shrinkage – those never become fully bright because of partial filling – and you end up at about half the true size. No single global level works across the product line because overall gain, tile density, blur width and noise floor all shift per batch. Counting bright voxels is a proxy; integrating total energy is the physical invariant.

Blur conserves counts. That is the key that allows sub-voxel recovery. But using it correctly is a small pipeline of its own: first get an unbiased estimate of background matrix level without letting the pore itself bias you, next get a robust estimate of background scatter (noise sigma), then isolate the main pore energy from the far specks, then get the real interior signal level that would be seen without blur and without being tricked by detector noise spikes, then grow outward to capture the faint halo belonging to the pore until the halos average excess falls into the noise while stopping before you accidentally bridge to a distant speck. Skipping halo capture causes systematic under-estimation because a large fraction of energy lives in the halo when scatter is wide; including specks causes over-estimation.

We grade to 3% relative error. Simple level methods are far outside that window.

Coding rules – your solve.py is scanned:
- Parse the binary yourself. Use only Python stdlib. Acceptable imports: struct, sys, math, random, tempfile, re.
- The following are forbidden and will make test_from_scratch fail: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, os, io, posixpath, ntpath, genericpath, and any other array, imaging or graph package.
- Forbidden builtins: eval, exec, compile, __import__, chr
- Forbidden runtime behaviour: subprocess, os.system, os.popen, os.exec, os.fork, os.walk, os.listdir, os.scandir, os.open, pty, importlib, runpy, ctypes, any directory listing, plus any trick to hide paths via chr, bytes.fromhex, base64, b64decode, bytearray or bytes([...]) or string concatenation building forbidden locations.
- Never try to open or list /tests, never mention test_outputs, heldout, reference_volume, _gen, GEOM_TRUTH, geometric_truth inside solve.py.
- Your program must work on any temporary file path, not a fixed path.

Print just the volume in mm³ as the last token. Example output line: 123.456
