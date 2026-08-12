I am a quality engineer for automotive chassis laser welding at a Tier one supplier. We join high strength steel with a six kilowatt laser. In some seams the vapor capillary becomes unstable and collapses into what we call a wormhole. It is a long interconnected hollow that snakes along the fusion line. It can weep fluid in service. We inspect every seam with inline computed tomography.

Our computed tomography is blurry. X ray point spread smears bright void signal into neighbours. So a wormhole looks thick and cloudy instead of crisp. That blur makes volume estimation hard.

Please create a tool that I can run. The tool lives at /app/solve.py. I will call it like python at /app/solve.py followed by a file path. I will take the last token you print as the answer in cubic millimetres.

I left one sample that you can use while coding at /app/data/scene.weld. Grading will use totally different files you have never seen. Those hidden files have assorted sizes, voxel pitch, brightness, weld orientation, noise level, and are handed to you as random paths in a temporary directory. Do not bake in any number you measure from the sample. Do not bake in any path string from the sample. Your code has to work for any path given.

The .weld container is my own minimal format. All numbers are little endian.

* First four bytes are ASCII WELD.
* Next four bytes are an unsigned int that holds format version.
* Next four bytes are an unsigned int that tells voxel type. Value 2 signals signed short int16 voxels. Value 16 signals float32 voxels. Both appear in grading.
* Next twelve bytes are three unsigned ints that tell voxel count per axis: nx then ny then nz.
* Next twelve bytes are three float32 that tell millimetre spacing per voxel: sx then sy then sz. You must read them, they differ file to file.
* Next four bytes are an unsigned int that tells byte offset where the voxel block starts. Do not assume 64, use what header says.
* From that offset onward lies nx times ny times nz voxel samples stored in announced type, with x changing fastest. For coordinate triple x y z the flat index is x plus nx times quantity y plus ny times z.

Inside each block the material is steel with two pore families that you must separate by shape after forming 26 neighbour connectivity components.

The family that matters for leak is wormhole. These are stitch channels that run for many voxels along the weld. Authoritative shape rule is an explicit elongation test on the axis aligned bounding box. For each 26 connectivity component compute dx = max_x - min_x + 1, dy = max_y - min_y + 1, dz = max_z - min_z + 1, sort ascending as d0 <= d1 <= d2, after first discarding flicker. Component is wormhole iff d2 >= 8 and d2 > 1.6 * d0. Descriptive guide only, this corresponds to strongly elongated in one or two axes. If several components satisfy the test, all are counted and their volumes summed. Example, extents 24, 8, 8 sort to 8, 8, 24 and 24 > 1.6*8 and >=8 so wormhole. Extents 6, 5, 5 sort to 5, 5, 6 and 6 < 8 so not wormhole.

The family to leave out is gas bubbles. These are compact near spherical artefacts trapped during solidification. Quantitatively they are exactly the negation of the wormhole test, namely d2 < 8 or d2 <= 1.6 * d0 after flicker removal. You must drop them by this shape test. No other elongation cutoff is valid.

Sensor flicker: occasionally one or two isolated bright dots appear far from the weld. They appear as 26 connectivity components with fewer than 30 voxels. You must discard any component with less than 30 voxels as flicker before applying the elongation test.

A wormhole voxel core is uniformly bright because X ray sees open space. At its skin the value is reduced by partial occupancy plus blur spill. The whole volume sits on a uniform background pedestal with additive sensor speckle.

Components for shape decision are formed over voxels whose residual after background subtraction exceeds three times the estimated noise sigma. This level is outcome determining and is stated explicitly so classification does not turn on tiny bridges that may appear at lower thresholds. If you try to binarise at a single fixed value for volume you will be wrong. A generous low limit sucks in the cloudy halo and inflates volume by near double. A stingy high limit clips the thin necks that never get fully bright and shrinks volume by about a third to half. No single limit works for volume because brightness and smear span change file to file. For volume you need conservation.

Only stitch wormhole voxels count toward the true measure; gas bubbles and far flicker are excluded. Grading checks within three percent across varied files, so you need a robust estimate that works despite brightness and blur variation. Recommended robust pipeline: estimate background as median of lower half to avoid void bias, estimate noise via MAD, estimate plateau via 3x3x3 filtered top-K mean to avoid hot spikes, integrate total energy including halo via growth until shell mean hits noise floor.

Code rules: you must parse raw bytes yourself. You may use only python standard library basic utilities: struct for unpacking, sys for args, math for numerics, random for any jitter if needed, tempfile for scratch if needed, re for text matching. Anything that does heavy lifting is forbidden. Forbidden imports include numeric and vision and graph stacks like numpy scipy skimage cv2 PIL Pillow networkx igraph imageio plus data stacks like pandas torch tensorflow plus system helpers like socket multiprocessing glob pathlib os io posixpath ntpath genericpath. If you import them your submission fails from scratch audit. Forbidden language tricks include eval exec compile __import__ chr for building strings. Forbidden operating system tricks include spawning processes via subprocess, calling os.system, os.popen, os.exec, os.fork, os.walk, os.listdir, os.scandir, os.open, using pty importlib runpy ctypes, listing directories. Builtin open is allowed to read the input file; os module itself is banned. Do not try to hide forbidden accesses via chr codes or via assembling strings from bytes fromhex base64 decoding or bytearray tricks or via concatenation that builds a path. Do not try to open or enumerate the directory /tests and do not mention test_outputs or heldout or _gen or GEOM TRUTH or geometric truth in your solver text. Your solver must function when given any random file path, not a fixed location.

When finished, output the estimated porosity in mm3 as the final whitespace separated token.
