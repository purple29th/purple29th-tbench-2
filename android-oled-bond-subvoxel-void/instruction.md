I work on Pixel watch oled lamination line where we hunt tiny trapped air that causes bonding failure. The bench has an under display infrared rig with vcsel diffuser that floods adhesive and a sensor that records backscatter. We dump the raw cube from an Android kotlin test that allocates a direct ByteBuffer little endian and writes via FileOutputStream to private app storage, same style as arcore depth dumps.

You need to produce the real air void size.

Create program at /app/solve.py that accepts one argument which is path to a scan file. When we execute python3 /app/solve.py /path/to/scan.obvl, your stdout last token must be a float that is the main void volume in cubic millimeters. There is a dev sample at /app/data/scene.obvl you can run locally. Hidden evaluation uses different scans you never saw, with different void sizes, diffuser power, voxel pitch, infrared background, noise level, dust fiber blobs. Do not hardcode any numbers from the dev sample.

File format is my own invented oled bond volume, magic OBVL.

Layout all little endian:

Bytes 0 to 3 is ascii OBVL
Bytes 4 to 7 is u32 version which is 1
Bytes 8 to 11 is u32 dtype code where 2 means int16 and 16 means float32
Bytes 12 to 23 is three u32 nx ny nz number of voxels per axis, total equals nx times ny times nz
Bytes 24 to 35 is three f32 sx sy sz physical mm per voxel, anisotropic because oled stack spreads wide in xy and bond is thin in z, different per file so you must read header, never assume constant
Bytes 36 to 39 is u32 data offset where voxel data starts, currently 64 but may have padding
Then at offset you have nx times ny times nz values of that dtype, x is fastest so index for coordinate x y z equals x plus nx times y plus nx times ny times z

Data contains one main bubble where air trapped plus sometimes zero to three far dust blobs that are fibre reflections not part of bubble. The vcsel plus oled stack gives anisotropic point spread, wide laterally narrow axially. Real shape is thick core that saturates to flat plateau after blur plus thin delamination fingers along x and y where voxel only partly filled so mid intensity that never reaches a usable threshold. Border voxels are dimmer from partial fill. There is flat ambient infrared background plus noise. To drop dust you must keep main connected component using 26 neighbours, but pick by integrated mass sum of background subtracted intensity, not voxel count, otherwise you may pick a dust speck.

Counting voxels above a threshold fails completely in this factory track. Low threshold includes huge halo and overestimates 70 to 120 percent. High threshold misses thin fingers and underestimates 30 to 50 percent. No fixed absolute or relative threshold works across files because diffuser power and background and pitch change per oled batch. The baseline from android depth object volume plus largest CC times spacing is 72 to 118 percent wrong here.

The trick that makes subvoxel precise: blur is normalized and conserves total photon counts, only spreads them. So you can get true occupancy by integrating background subtracted intensity over void plus halo and dividing by plateau amplitude where plateau is saturated interior where scatter most concentrated. You need to figure out robust estimation for background floor and plateau level and halo extent without bridging to far specks.

Implement parsing and labeling and integration from scratch. Allowed imports are struct and sys only for final program, plus math if needed. Do not use numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow. Also do not use any shell or filesystem traversal tricks like subprocess with system popen exec walk listdir scandir open stat read fdopen path, nor pathlib or io open or shutil, nor dynamic tricks like getattr setattr hasattr globals locals vars dir chr ord base64 binascii codecs, nor dunder builtins dict subclasses mro etc beyond name main check, and do not open or read tests directory or heldout files. We audit source for obfuscated paths.

At the end print volume as last token. Grading uses 3 percent tolerance versus independent conservation reference that has different constants than oracle and matches geometric truth within about one percent.

Apply anisotropic pitch multiplication sx times sy times sz or you fail volume. Use handwritten 26 neighbour BFS.

Author note: Pixel OLED bonding factory QA track.
