I am Anya from Yakutsk in Sakha, my father studies permafrost methane in Batagay crater. Batagay is biggest permafrost crater and grows each year because permafrost thaws. In summer we drill one meter ice cores at one am when sun is still up but air is minus ten and image methane bubbles that glow with infrared dye we inject at minus five. The rig writes PMBF file I call permafrost methane bubble flux, magic PMBF.

I need a small tool that tells me total methane bubble flux in mg per m2 per day for all elongated bubbles along ice veins that are real flux. Some cores have two distant bubble fields far apart that both matter, you must sum them. Biggest only fails forty to fifty percent.

Please make file at /app/solve.py. We call python /app/solve.py path to scan and final token is answer.

There is one example you can try at /app/data/scene.pmbf inside container, about seven twenty nine mg per m2 per day. Hidden evaluation uses totally different cores I made with new sizes spacings defect thickness brightness diffusion and pitch with random temp file names like input_a3f9.pmbf. So you cannot hardcode.

File layout pmbf. My own tiny format little endian.

Four bytes ascii PMBF.
Four bytes uint32 version.
Four bytes uint32 dtype code. Two means int16 voxels, sixteen means float32 voxels.
Twelve bytes are three uint32 nx ny nz counts per axis.
Twelve bytes are three float32 sx sy sz mm per voxel, this changes per file so you must read it.
Four bytes uint32 data offset where voxel array starts, can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty that scales final flux sample one point zero hidden at ninety six uses one point two two ignore and you fail by twenty two percent.
At data offset you get nx times ny times nz samples in dtype announced, X fastest.

Inside each cube elongated methane bubbles along ice veins that count. There are also compact water inclusion pores that are almost spherical and benign you must not count them. Some scans also have one to three very tiny bright dots far away that are drill dust on auger window, ignore them.

We use twenty six neighbour connectivity in three dimensions, that means twenty six around.

Calibration flux equals volume mm3 times zero point seven two mg per m2 per day per mm3 times multiplier. So you first recover true bubble volume from smeared cloud, then multiply.

I tried naive brightness levels and they are hopeless. If I am generous and count everything slightly above background my flux nearly doubles. If I am strict and only count very bright voxels I lose thin tails and lose third to half. Each file has different background gain and scatter width, no fixed level works.

Energy is preserved despite smear. Total excess stays same, so bright counting fails but conservation idea can work if you handle background bias that is pulled by defect, noise floor that varies per core, far dust that must be ignored, interior level hidden by blur. You also must avoid counting skirt as background and avoid jumping to distant specks, sum all separate elongated pieces not just biggest.

If you get background and interior right you land within percent, grading allows three percent.

Coding rules. You must parse bytes yourself only stdlib. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array imaging or graph library. Banned calls include eval exec compile import chr ord breakpoint bytes bytearray. Banned tricks include subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray tricks. Do not try to open or list tests folder. Do not reference test_outputs heldout _gen geometric_truth in solver. Your solver must work on any random temp path.

Print flux mg per m2 per day as last printed token.
