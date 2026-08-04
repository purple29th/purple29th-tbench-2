I look after EUV pellicles for the scanner. The pellicle is a freestanding ten nanometer film that covers the reticle and keeps particles away. After many EUV shots with thirteen point five nanometer light, cracked pump oil and resist outgas form dark carbon veins on the film. The veins absorb EUV, the film heats and can break, so we track total carbon in micrograms to decide replacement.

My setup shines X-ray and collects fluorescence that is bright where carbon sits. The trouble is the scintillator spreads charge and the lens adds its own point spread, so each vein appears as a big soft cloud that is much bigger than the true carbon. You get one example file at /app/data/scene.epcm to try locally. The hidden grading uses completely new cubes I made with different sizes, membrane pitch, vein width, brightness, background, and scatter, passed as random temp files like input_9f3a.epcm. You cannot hardcode numbers from the example.

File epcm is my own tiny format, everything little endian.

Four bytes ascii EPCM.
Four bytes uint32 version.
Four bytes uint32 dtype code. Two means int16 voxels, sixteen means float32 voxels.
Twelve bytes are three uint32 nx ny nz counts per axis.
Twelve bytes are three float32 sx sy sz millimeters per voxel, this changes per file so you must read it.
Four bytes uint32 data offset where voxel array starts.
At data offset you get nx times ny times nz samples in the dtype announced, X fastest, so linear index is x plus nx times y plus ny times z.

What lives inside. Each cube has a few carbon deposits. The ones that matter for scanner dose are the long branching veins that track crazing lines on the film. Those are the only carbon that counts for the mass I want. There are also compact fallout dots that are almost round and come from airborne particles, those are benign and must be ignored. Veins are stretched, fallout is compact. In lab we keep a vein when its bounding box longest side is at least eight and more than one point six times its shortest side. Fallout is cubic. Some scans also have one to three very tiny bright dots far away that are dust on the camera window, ignore them.

We use twenty six neighbour connectivity in three dimensions.

Calibration: we took a known vein, ashed it in oxygen plasma and weighed it. We measured two point one micrograms per cubic millimeter of solid carbon. So you first recover true vein volume in cubic millimeters from the smeared cloud, then multiply by two point one to get micrograms.

I tried naive brightness levels and they are hopeless. If I am generous and count everything slightly above background I swallow the whole aureole and my mass nearly doubles. If I am strict and only count very bright voxels I lose the feathered tips that are thin and never reach full brightness because of partial occupancy and I lose a third to half. Each file has different background, gain, and scatter width, so no fixed level works.

What does work is energy preservation. The scatter does not create fluorescence, it only moves it. So if you add up all background removed glow over vein plus its faint skirt and divide by true interior brightness, you get true voxel count even though blurred. To make that work you need a clean background estimate from the median of the whole stack and a noise estimate from median absolute deviation of the lower half, you need to seed bright voxels above four sigma and grow twenty six connected blobs, keep the stretched veins via stretch test and drop the compact dots, you need a robust interior level by smoothing each candidate with three by three by three neighbourhood mean then averaging the top four inside main veins, and you need to grow outward shell by shell until average shell glow falls to about noise floor, skipping artefact voxels so you do not jump into a dust ball.

If you do those steps you land within a percent, grading allows three percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr. Banned runtime tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list the tests folder. Do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH geometric_truth in your solver. Your solver must work on any random temp path.

Print mass in ug as last printed token.
