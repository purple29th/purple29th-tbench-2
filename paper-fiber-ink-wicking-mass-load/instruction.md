I work on coated paper QC for inkjet media. The paper has fibers that wick ink sideways, creating an irregular feathered ink pool that follows fiber direction. We map ink with UV fluorescence where ink glows bright, but fiber capillary diffusion plus lens smear makes the glow look much larger and fuzzier than true ink that actually sits in coating.

I need a small tool that tells me total ink wicking mass in milligrams for all irregular pools that are the real ink. Some sheets have two separate irregular pools far apart that both count, you must sum their areas first then convert to mass.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read final printed token as answer.

There is one example map you can try at /app/data/scene.inkw inside container. That is just for you to debug. Hidden evaluation uses completely different maps I made with new sizes spacings pool thickness brightness diffusion and pitch passed as random temp file names. So you cannot hardcode numbers from example. If you hardcode example you will fail hidden.

File layout inkw. My own tiny format, everything little endian.

Our scanner writes a custom container with extension inkw. All numbers are little endian. File begins with four ascii bytes INKW as tag. Then uint32 version. Then uint32 dtype id where two means pixels are int16 and sixteen means pixels are float32. Then two uint32 nx ny pixel counts. Then two float32 sx sy millimeters per pixel anisotropic and change per sheet, you must read them. Then uint32 data offset that tells where pixel payload begins and varied so it can be thirty two forty forty eight sixty four eighty ninety six one twenty eight, so please respect field. Then float32 gain trim at offset forty that multiplies mass and varies zero point eight five to one point three five per file and must be read and applied, sample file has gain one so effect hidden but hidden uses non unit gain. Then the rest up to data offset is padding.

At data offset you get nx times ny samples in dtype announced, X fastest, linear index is x plus nx times y.

Inside each map there is ink in a few places. The ink that counts is irregular feathered pools that follow fiber direction that are the only ink that counts. There are also round water droplets that are near circular and must be ignored. Some sheets have two separate irregular pools far apart that both count and must be summed for total area. You must use eight neighbour connectivity and bounding box measured on bright mask above four sigma noise level. In lab we keep a pool when its bounding box measured on that bright mask has longest side at least ten and more than one point six times shortest side and at most thirty five. That keeps irregular and drops round where longest at most one point six times shortest.

Some scans also have one to three very tiny bright specks far away from dust on window that must be ignored.

We use eight neighbour connectivity.

Calibration: lab shows each square millimeter of ink holds zero point eight five milligrams times gain trim. So mass in mg equals area mm2 times zero point eight five times gain. You first recover true ink area from smeared cloud, then compute mass.

Naive levels are hopeless. If I am generous and count everything slightly above background my area balloons and my mass nearly doubles. If I am strict and only count very bright pixels I lose thin feathered edges and I lose third to half. Each file has different background gain and scatter width.

Energy preservation works. Total glow over pool plus faint skirt divided by true interior brightness gives true pixel count.

If you get background and interior right you land within a percent, grading allows three percent.

Coding rules. You must parse bytes yourself, only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile __import__ chr ord breakpoint bytes bytearray. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH geometric_truth in solver. Your solver must work on any random temp path.

Print mass in mg as last printed token.
