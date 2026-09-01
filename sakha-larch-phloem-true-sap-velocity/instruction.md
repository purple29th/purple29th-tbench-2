I am Ayta from Batagay in Verkhoyansk. My grandmother is Evenk and herds reindeer near the Yana river. In winter it is minus fifty two and we still go to the taiga to mark larch for resin. At night we cut a thin phloem slab zero point three mm thick and drip fluorescein tracer that moves with sap. I have a hamamatsu camera in a heated yurt that photographs the slab at one am. The tracer glows but ice fog and lens smear the glow far beyond true streak.

I need a small tool that tells me true sap flow velocity in mm per second for all elongated tracer streaks that are real flow. Some slabs have two distant streaks far apart that both count, you must sum them. If you keep only biggest you lose forty to fifty percent.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read final printed token as answer.

There is one example slab you can try at /app/data/scene.sapf inside container, about nineteen mm per second. Hidden evaluation uses completely different slabs I made with new sizes spacings defect thickness brightness diffusion and pitch passed as random temp file names like input_a3f9.sapf. So you cannot hardcode numbers from example.

File layout sapf. My own tiny format, everything little endian.

Four bytes ascii SAPF.
Four bytes uint32 version.
Four bytes uint32 dtype code. Two means int16 voxels, sixteen means float32 voxels.
Four bytes uint32 width nx.
Four bytes uint32 height ny.
Four bytes float32 sx mm per voxel x.
Four bytes float32 sy mm per voxel y.
Four bytes uint32 data offset where voxel array starts, can be forty eight sixty four eighty ninety six one twenty eight.
Twelve bytes padding zeros between twenty eight and forty.
Four bytes float32 multiplier at offset forty that scales final answer, changes per file, sample is one point zero, hidden lot at ninety six uses one point two two, ignore and you fail by twenty two percent.
At data offset you get nx times ny samples in dtype announced, X fastest, linear index is x plus nx times y.

Inside each slab there is larch phloem flow in a few places. Real flow is elongated along grain that are the only ones that count. There are also compact bacterial autofluorescence that is almost round and benign, you must not count it. Some scans also have one to three very tiny bright dots far away that are frost on yurt window, ignore them.

We use eight neighbour connectivity in two dimensions.

Calibration. Larch vessel width is zero point three zero mm and exposure is zero point six zero seconds, so velocity in mm per second equals area mm2 divided by zero point three zero divided by zero point six zero times multiplier. So you first recover true area from smeared cloud, then convert to velocity. Area itself is count times sx times sy, count is true pixel count from energy conservation.

I tried naive brightness levels and they are hopeless. If I am generous and count everything slightly above background my velocity nearly doubles. If I am strict and only count very bright voxels I lose thin tails and I lose third to half. Each file has different background gain and scatter width, so no fixed level works.

Energy is preserved despite smear. Total excess stays same, so bright counting fails but a conservation idea can work if you handle background bias that is pulled by the defect, the noise floor that varies per slab, the far frost that must be ignored, and the interior level hidden by blur. You also must avoid counting skirt as background and avoid jumping to distant specks, and you must sum all separate elongated pieces not just the biggest.

If you get background and interior right you land within a percent, grading allows three percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile import chr ord breakpoint bytes bytearray. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference in solver. Your solver must work on any random temp path.

Print velocity in mm per second as last printed token.
