I work on a PV line inspecting monocrystalline wafers after cell stringing. When a wafer has a microcrack, that region is electrically dead and shows up dark in electroluminescence imaging. We photograph the wafer with a cooled silicon CCD.

EL imaging lies though. Injected carriers diffuse laterally before radiative recombination, and the lens has a small point spread. The combination keeps total dark deficit the same but smears it outward into a wide gray halo. So a hairline crack that is truly 1.2 square millimetres looks like a big fuzzy cloud of 2.5 square millimetres. Buyers care about true dead area in square millimetres, not the cloud.

You have to write the measuring tool.

Save it at /app/solve.py. It will be run as python /app/solve.py with a scan path argument. The last whitespace token printed on stdout is taken as the area.

We give you one wafer to develop on at /app/data/scene.elcr. You may open it locally. Hidden grading uses completely different wafers that differ in image size, pixel pitch, crack shape, EL brightness, background luminescence, diffusion length, and noise. Files are passed as random temporary paths. Do not hardcode numbers or absolute paths from the example file. Hardcoding the example area makes hidden checks fail.

The file format is ELCR, a custom binary for EL crack area, all little endian. The first four bytes are ASCII magic ELCR. Bytes four to seven hold uint32 version. Bytes eight to eleven hold uint32 dtype tag where two means int16 pixels and sixteen means float32 pixels. Bytes twelve to nineteen hold two uint32 dimensions nx ny which are pixels along x and y. Bytes twenty to twenty seven hold two float32 scales sx sy in millimetres per pixel. These are anisotropic and file dependent so you must read them. Bytes twenty eight to thirty one hold uint32 offset where pixel block starts. From that offset onward there are nx times ny samples in declared dtype, x moves fastest, linear index is x plus nx times y. Dark crack was already inverted to bright during export so the defect appears bright on top of flat background.

Each file holds one main crack network that determines the grade. A few files also contain extra tiny bright spots far away from dust or edge chipping. Those far spots are not part of the main crack and must be excluded from the measurement.

Why naive bright counting gives wrong answers. A permissive cutoff includes the surrounding diffuse fringe and ends up roughly twice the true size. A strict cutoff keeps only the brightest core and loses thin branching that never gets fully bright and ends up roughly half the true size. No single cutoff works across production because gain, background, diffusion length and noise all shift. The fuzzy look is the clue that energy has been spread.

Even though the image looks blurred, total signal is still there. Blur moves it around but does not create or destroy it. That physical preservation is what makes an accurate area possible despite smear. Using it well means dealing with background influence, isolated far artefacts, and deciding where the faint edge really ends. That combination is where most simple methods break.

We grade at three percent relative error. Simple level methods are far outside that window.

Coding rules, your solve.py is scanned. Parse the binary yourself. Allowed imports only are struct sys math random tempfile re. Forbidden libraries and will fail test_from_scratch are numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath plus any other array imaging or graph helper. Forbidden calls are eval exec compile import with double underscores and chr. Forbidden runtime includes subprocess, os dot system, os dot popen, os dot exec, os dot fork, os dot walk, os dot listdir, os dot scandir, os dot open, pty, importlib, runpy, ctypes, any directory listing, plus tricks hiding paths via chr, bytes dot fromhex, base64, b64decode, bytearray, bytes list or string concatenation building forbidden locations. Do not try to open or list the tests directory and do not mention test_outputs, heldout, reference_volume, underscore gen, GEOM_TRUTH, geometric_truth in solve.py. Must work on any temporary file path, not a fixed path.

Print the dead area in square millimetres as the last token. Example line is 12.345
