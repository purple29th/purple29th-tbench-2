I work on PCB signal integrity for server boards. High speed differential pairs run over FR4 prepreg. When prepreg has tiny voids where resin is missing the capacitance between P and N goes up and impedance drops. We catch this with X-ray fluorescence where missing resin glows bright, but diffusion plus lens smear makes the glow look much bigger than true void.

I need a small tool that tells me total added capacitance in picofarads for all elongated voids along trace direction. Some boards have two separate elongated voids far apart that both count, you must sum their volumes first then convert to capacitance.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read final printed token as answer.

There is one example volume you can try at /app/data/scene.capv inside container. That is just for you to debug. Hidden evaluation uses completely different volumes I made with new sizes spacings defect thickness brightness diffusion and pitch passed as random temp file names. So you cannot hardcode numbers from example. If you hardcode example you will fail hidden.

File layout capv. My own tiny format, everything little endian.

Our scanner writes a custom container with extension capv. All numbers are little endian. File begins with four ascii bytes CAPV as tag. Then uint32 version. Then uint32 dtype id where two means voxels are int16 and sixteen means voxels are float32. Then three uint32 nx ny nz counts per axis. Then three float32 sx sy sz millimeters per voxel anisotropic and change per board, you must read them. Then uint32 data offset that tells where voxel payload begins and varied so it can be thirty two forty forty eight sixty four eighty ninety six one twenty eight, so please respect field. Then float32 gain trim at offset forty that multiplies capacitance and varies zero point eight five to one point three five per file and must be read and applied, sample file has gain one so effect hidden but hidden uses non unit gain. Then the rest up to data offset is padding.

At data offset you get nx times ny times nz samples in dtype announced, X fastest, linear index is x plus nx times y plus ny times z.

Inside each cube there is missing resin in a few places. The voids that count are elongated voids that run along trace direction that are the only voids that count. There are also round lamination bubbles that are near spherical and must be ignored. Some volumes have two separate elongated voids far apart that both count and must be summed for total volume. You must use twenty six neighbour connectivity and bounding box measured on bright mask above five sigma noise level. In lab we keep a void when its bounding box measured on that bright mask has longest side at least twelve and more than two times shortest side and at most thirty five. That keeps elongated and drops round where longest at most one point six times shortest.

Some scans also have one to three very tiny bright specks far away from dust on window that must be ignored.

We use twenty six neighbour connectivity.

Calibration: lab shows each cubic millimeter of missing resin adds zero point nine two picofarads times gain trim. So capacitance in pF equals volume mm3 times zero point nine two times gain. You first recover true void volume from smeared cloud, then compute capacitance.

Naive levels are hopeless. If I am generous and count everything slightly above background my volume balloons and my capacitance nearly doubles. If I am strict and only count very bright voxels I lose thin tails and I lose third to half. Each file has different background gain and scatter width.

Energy preservation works. Total glow over void plus faint skirt divided by true interior brightness gives true voxel count.

If you get background and interior right you land within a percent, grading allows three percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr ord breakpoint bytes bytearray. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH geometric_truth in solver. Your solver must work on any random temp path.

Print capacitance in pF as last printed token.
