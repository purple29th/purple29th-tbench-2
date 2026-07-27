hey i am in a fab doing laser etch on silicon wafers. we fire a short laser pulse to etch tiny pits for photonic crystals, then we image the wafer with a thermal IR camera right after the pulse. the pits trap heat and glow, but heat diffusion plus the IR optics smears the glow all over, so the pit looks much bigger and fuzzier than the real etched area.

i need a program that tells the true physical etched area in square mm, not the smeared thermal glow. this matters for etch quality and photonic bandgap.

make file named solve.py inside app folder. we call it as python app solve.py with scan path as argument. last word printed is taken as area.

you get one example to try named scene.weta inside data folder that is inside app folder. you may read that file while developing, but hidden grading uses different scans you have never seen that vary in grid size, pixel pitch, etch depth, wafer background temperature, and thermal blur, passed as random temporary files. do not hardcode numbers or paths from example.

what is weta. our own small binary for wafer etch thermal area. everything little endian.

file starts with four ascii W E T A.

version is next four bytes unsigned thirty two little endian.

dtype code next four bytes unsigned thirty two little endian. code 2 means int16 pixels, code 16 means float32 pixels.

next eight bytes are two unsigned thirty two counts of pixels per axis, historically nx, ny.

next eight bytes are two float32 values for mm per pixel per axis, historically sx, sy. they change per file so you must read them.

next four bytes unsigned data offset where pixels start.

after data offset you have nx times ny values in announced dtype, x fastest, so index for x,y is x plus nx times y.

inside is one solid etch pit where silicon was removed. centre is flat hot where heat is trapped and IR signal saturates. border is dimmer with partial fill smeared by thermal diffusion. flat wafer background plus sensor noise. some scans have one or two tiny hot specks far away from particle contamination, ignore them and keep only the main connected hot mass using eight neighbours.

this is tricky and can be hard to get precise. hot pixel counting is never precise. a permissive cutoff includes huge faint halo and inflates a lot, a strict cutoff misses thin micro cracks that never get hot enough and deflates a lot. no fixed cutoff works across files because etch depth, wafer temperature, and diffusion width change per scan.

accurate measurement despite blur needs careful handling of background, far specks, and faint tails. separating main pit from distant contamination, getting unbiased wafer level, and deciding where the faint thermal edge really ends without merging dust are the hard parts where most shortcuts fail. thin feathered etch extensions are only slightly hotter than wafer, never fully hot.

simple counting heuristics are far outside tolerance. grading uses three percent relative tolerance, only careful reconstruction that handles diffusion and noise meets it.

implementation rules: parse bytes yourself with only standard library. allowed modules include struct, sys, math, random, tempfile, re. the following are banned and checked in test_from_scratch: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, os, io, posixpath, ntpath, genericpath, tarfile, zipfile. banned calls include eval, exec, compile, __import__, chr, open. also forbidden are runtime tricks like subprocess, os.system, os.popen, filesystem listing via walk, listdir, scandir, rglob, glob(), and path hiding via chr(), bytes.fromhex, base64, b64decode, bytearray, bytes([...]) patterns. do not try to open or list /tests and do not reference test_outputs, heldout, reference, _gen, GEOM_TRUTH, geometric_truth, reference_volume in your solver source. solver must work on random temporary files, not hardcoded locations. note: in this variant even the builtin open is flagged to force use of low level file reading via os.open or io? Actually we ban open to add edge that meta code fails, but you must use os.open and os.read and io.FileIO? Wait we say banned open, so you must use os.open low level? The edge is that avocado often uses open() which will now fail from scratch, so you must use os.open and os.read. Make sure to handle.

print area mm2 as last token.
