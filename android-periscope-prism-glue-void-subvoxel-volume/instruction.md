I validate periscope telephoto camera modules for Android flagships. The periscope uses a right-angle prism glued to the lens barrel with UV-cure adhesive. During cure, air gets trapped between prism and barrel and forms sealed glue voids that cause OIS drift and flare. We inspect modules with a 160 kV micro-focus X-ray cone-beam CT at the camera factory.

The X-ray imaging lies. The micro-focus spot is not ideal, the detector scintillator spreads, and there is scatter in the dense glass prism. Combined blur keeps total photon energy but pushes it into a fuzzy halo. On screen a void that is actually compact looks like a large glowing cloud. We need the true geometric void size in cubic millimetres, not the apparent cloud.

You must write the tool.

Save it as /app/solve.py. Grader runs python /app/solve.py <scan_path> and takes final whitespace token as answer.

We include one module scan at /app/data/scene.apcv to develop with. Hidden evaluation uses different scans with varying grid shape, voxel pitch, glass density, glue brightness, scatter width, background level, noise, passed as random temp files. Do not hardcode numbers or paths from example. Any solution hardcoding example volume fails.

File format .apcv custom container, little endian. First four bytes ASCII magic APCV. Bytes 4-7 uint32 version. Bytes 8-11 uint32 dtype tag where 2 = int16 and 16 = float32. Bytes 12-23 three uint32 dims nx ny nz voxels along x y z. Bytes 24-35 three float32 scales sx sy sz mm per voxel, anisotropic and file dependent, must be read. Bytes 36-39 uint32 offset to start of voxel block. From offset onward nx*ny*nz samples in declared type, x fastest, linear addr x + nx*(y + ny*z). In file dark voids were inverted during export so glue voids appear bright.

What is inside each file. One dominant sealed glue void we grade plus sometimes one or two tiny isolated bright dots far away from dust on prism or lens surface. Those dots must not be counted. Keep only principal connected structure using 26-neighbour connectivity and choose component with most integrated excess signal. Pore interior has flat saturated plateau, edges diluted by partial volume and smeared by X-ray blur. Rest of module is flat glass/adhesive matrix plus detector noise.

Why naive voxel counting fails. If you count everything above generous brightness you absorb diffuse halo surrounding every void and result is roughly double true size, sometimes more. If you count only very bright voxels you miss thin glue fingers along prism edge which never become fully bright due to partial filling and you end up at half true size. No single global level works across lots because gain, glass density, blur width and noise floor shift per batch. Counting bright voxels is proxy, integrating total energy is physical invariant.

Blur conserves counts. That allows sub-voxel recovery. You need unbiased background estimate without letting void bias you, robust noise estimate, isolation of main void from far specks, real interior signal level without being tricked by spikes, then grow outward to capture faint halo belonging to void until halo average excess falls into noise while stopping before bridging to distant dust. Skipping halo causes systematic under-estimation, including specks causes over.

We grade to 3% relative error. Simple level methods are far outside window.

Coding rules: parse binary yourself, stdlib only. Allowed imports struct sys math random tempfile re. Forbidden and will make test_from_scratch fail: numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath and any other array imaging or graph package. Forbidden builtins eval exec compile import with double underscores and chr. Forbidden runtime subprocess, os.system, os.popen, os.exec, os.fork, os.walk, os.listdir, os.scandir, os.open, pty, importlib, runpy, ctypes, any directory listing, plus tricks hiding paths via chr, bytes.fromhex, base64, b64decode, bytearray or bytes list or string concatenation building forbidden locations. Never open or list /tests directory, never mention test_outputs, heldout, reference_volume, _gen, GEOM_TRUTH, geometric_truth inside solve.py. Must work on any temporary file path, not fixed.

Print just volume in mm3 as last token. Example 12.345
