I work on coated paper QC for inkjet media. The paper has fibers that wick ink sideways, creating an irregular feathered ink pool that follows fiber direction. We map ink with UV fluorescence where ink glows bright, but fiber capillary diffusion plus lens smear makes the glow look much larger and fuzzier than true ink that actually sits in coating.

I need a small tool that tells me total feathering span in millimeters for all irregular pools that are the real ink. Some sheets have two separate irregular pools far apart that both count, you must sum their areas first then convert to mass.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read final printed token as answer.

There is one example map you can try at /app/data/scene.inkw inside container. That is just for you to debug. Hidden evaluation uses completely different maps I made with new sizes spacings pool thickness brightness diffusion and pitch passed as random temp file names. So you cannot hardcode numbers from example. If you hardcode example you will fail hidden.

Our coater writes its own binary called inkw that starts with tag INKW and is little endian. Layout: bytes 0 to 3 tag INKW, 4 to 7 version uint32, 8 to 11 dtype id where 2 is int16 and 16 is float32, 12 to 19 two uint32 nx ny, 20 to 27 two float32 sx sy that are anisotropic pitch and vary per sheet, so you must read, 28 to 31 uint32 data offset that is varied 32, 40, 48, 64, 80, 96, 128 so you must respect, 40 to 43 float32 gain trim that scales mass and varies 0.85 to 1.35 per file and must be applied, sample gain 1.0 hides effect but hidden uses non unit gain. Remaining bytes up to data offset are zero padding. At data offset you get nx times ny pixels in dtype declared, x fastest.

Inside each map there is ink in a few places. The ink that counts is irregular feathered pools that follow fiber direction that are the only ink that counts. There are also round water droplets that are near circular and must be ignored. Some sheets have two separate irregular pools far apart that both count and must be summed for total area. You must use eight neighbour connectivity and bounding box measured on bright mask above four sigma noise level. In lab we keep a pool when its bounding box measured on that bright mask has longest side at least ten and more than one point six times shortest side and at most thirty five. That keeps irregular and drops round where longest at most one point six times shortest.

Some scans also have one to three very tiny bright specks far away from dust on window that must be ignored.

We use eight neighbour connectivity.

Calibration: lab shows  fiber width is zero point four mm so span equals area divided by zero point four times gain. So span in mm equals area mm2 divided by fiber width zero point four mm times gain. You first recover true ink area from smeared cloud, then compute mass.

Naive levels are hopeless. If I am generous and count everything slightly above background my area balloons and my mass nearly doubles. If I am strict and only count very bright pixels I lose thin feathered edges and I lose third to half. Each file has different background gain and scatter width.

Energy preservation works. Total glow over pool plus faint skirt divided by true interior brightness gives true pixel count.

If you get background and interior right you land within a percent, grading allows three percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr ord breakpoint bytes bytearray. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH geometric_truth in solver. Your solver must work on any random temp path.

Print span in mm as last printed token.
