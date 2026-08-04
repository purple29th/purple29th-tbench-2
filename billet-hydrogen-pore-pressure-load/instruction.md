I work on continuous cast aluminum billet inspection. Hydrogen from humidity gets into the melt and during solidification it forms round sealed pores that hold pressurized gas. When we extrude, those pores open as surface blisters that fail QA. I need to know internal gas pressure in kilopascals to decide which billets need degas.

We image hydrogen with fluorescence where pores glow bright, but diffusion in the scintillator plus lens smear makes the glow look much bigger than true pore, so counting bright voxels gives double volume.

I need a small tool that tells me total gas pressure in kPa for all round pores together. Pressure depends on total volume, so if you sum correctly you get pressure. Some volumes have two separate round pores far apart that all count, you must sum their volumes first then convert to pressure via constant divided by volume.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read final printed token as answer.

There is one example volume you can try at /app/data/scene.hprr inside container. That is just for you to debug. Hidden evaluation uses completely different volumes I made with new sizes spacings defect thickness brightness diffusion and pitch passed as random temp file names. So you cannot hardcode numbers from example. If you hardcode example you will fail hidden.

Our scanner writes a custom container with extension hprr. All numbers are little endian in file. The file begins with four ascii bytes HPPR that act as tag. Then we have a uint32 version field. Then a uint32 dtype id where two means voxels are int16 and sixteen means voxels are float32. Then three uint32 giving nx ny nz voxel counts per axis. Then three float32 sx sy sz that are millimeters per voxel and are anisotropic and change per billet heat, you must read them from header, not assume constant. Then a uint32 data offset that tells where the voxel payload begins and our writer uses varied padding so offset can be thirty two forty forty eight sixty four eighty ninety six one twenty eight, so please respect the field. After that offset you have nx times ny times nz samples in the dtype declared, x is fastest so linear equals x plus nx times y plus ny times z.

Inside each cube there is hydrogen in a few places. The pores that count are round sealed pores that are near spherical from hydrogen, those are the only pores that count. There are also elongated manganese sulfide stringers that are long along casting direction and must be ignored. Some volumes have two separate round pores far apart that all count and must be summed for total volume. You must use twenty six neighbour connectivity and bounding box measured on bright mask above eight sigma noise level. In our lab we keep a pore when its bounding box measured on that bright mask has longest side at most thirty five and longest at most three times shortest side. That keeps round pores even after anisotropic PSF smears a five by five by five pore to about twenty by fifteen by ten, and drops stretched sulfide stringers where longest at least twelve and more than three times shortest which become twenty by six by six after smear. That is inverted versus many tasks that kept elongated. Some scans also have one to three very tiny bright specks far away from dust on window that must be ignored.

We use twenty six neighbour connectivity.

Calibration: lab shows we injected a known amount of hydrogen, ideal gas law gives constant seven hundred eighty kilopascal cubic millimeter. So pressure in kPa equals seven hundred eighty divided by total pore volume in cubic millimeters. You first recover true pore volume from smeared cloud, then compute pressure.

Naive levels are hopeless. If I am generous and count everything slightly above background my volume balloons and my pressure collapses because pressure is inverse of volume. If I am strict and only count very bright voxels I lose thin edges and my volume shrinks and my pressure spikes. Each file has different background gain and scatter width.

Energy preservation works. Total glow over pore plus faint skirt divided by true interior brightness gives true voxel count.

If you get background and interior right you land within a percent, grading allows three percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH geometric_truth in solver. Your solver must work on any random temp path.

Print pressure in kPa as last printed token.
