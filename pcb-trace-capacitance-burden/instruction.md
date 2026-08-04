I work on PCB signal integrity for server boards. High speed differential pairs run over FR4 prepreg. When prepreg has tiny voids where resin is missing the capacitance between P and N goes up and impedance drops. We catch this with X-ray fluorescence where missing resin glows bright, but diffusion plus lens smear makes the glow look much bigger than true void.

I need a small tool that tells me total added capacitance in picofarads for all elongated voids along trace direction. Some boards have two separate elongated voids far apart that both count, you must sum their volumes first then convert to capacitance.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read final printed token as answer.

There is one example volume you can try at /app/data/scene.capv inside container. That is just for you to debug. Hidden evaluation uses completely different volumes I made with new sizes spacings defect thickness brightness diffusion and pitch passed as random temp file names. So you cannot hardcode numbers from example. If you hardcode example you will fail hidden.

Container layout capv is little endian with tag CAPV. Byte ranges: zero to three tag CAPV, four to seven version uint32, eight to eleven dtype id where two is int16 and sixteen is float32, twelve to twenty three three uint32 nx ny nz, twenty four to thirty five three float32 sx sy sz that are anisotropic pitch and vary per board, so you must read, thirty six to thirty nine uint32 data offset that is varied thirty two forty forty eight sixty four eighty ninety six one twenty eight so you must respect, forty to forty three float32 gain trim that scales capacitance and varies zero point eight five to one point three five per file. Remaining bytes up to data offset are zero padding. At data offset you have nx times ny times nz samples in dtype declared, x fastest so linear is x plus nx times y plus ny times z.

What should be counted. Inside each cube there is missing prepreg resin in several spots. Voids that matter are elongated resin starvation along trace that run along weave, those count for pF. Round lamination bubbles from lamination are near spherical and must be ignored. Some boards have two separate elongated voids far apart that both count and must be summed for total volume before pF conversion. So keeping only biggest fails.

How I decide shape in lab. I first build bright mask where residual above five sigma after background removal. I measure bounding box on that mask. I keep a void when its box has longest at least twelve and more than two times shortest and at most thirty five, which keeps long weave voids and drops compact bubbles that are at most one point six times shortest. That is ordinary PCB check.

Calibration. Lab measured that each cubic millimeter of missing resin adds zero point nine two picofarads times gain trim. So pF equals volume mm3 times zero point nine two times gain. You first recover true void volume from smeared cloud, then compute pF.

Simple threshold is useless. Low level swallows whole aureole and my pF roughly doubles. High level clips thin tails along weave that are dim due to partial volume and I lose third to half. Each board has different background, gain, scatter.

What does work is that total excess glow over void plus its faint skirt divided by core brightness equals true voxel count, energy preserved.

If you get background and interior right you land within a percent, grading allows three percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr ord breakpoint bytes bytearray. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH geometric_truth in solver. Your solver must work on any random temp path.

Print capacitance in pF as last printed token.
