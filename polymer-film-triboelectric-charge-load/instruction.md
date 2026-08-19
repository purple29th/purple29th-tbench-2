I work in polymer film QC checking roll to roll lines. When the film moves fast it gets triboelectrically charged in patches along the draw direction. Charged patches attract dust and cause coating defects. I map surface potential with a Kelvin probe where charge shows bright but probe diffusion plus lens blur smears the signal so the patch looks much larger and fuzzier than the true charged area that actually holds dust.

I need a small tool that tells me total triboelectric charge in nanoCoulombs for the main elongated patch. Precision matters because we grade ESD risk per roll.

Please save your program as /app/solve.py. We will run it as python /app/solve.py with the scan path as first argument and we take the last word printed as charge.

You have one example scan for local testing at /app/data/scene.trch. You can read it while you develop but hidden grading uses different scans you never saw with different dimensions spacings brightness patch thickness and pixel pitch passed as random temp files. Do not hardcode numbers from the example. Your solver must work on any file path given as first argument. Hardcoding sample charge will fail.

What is trch. Our own binary for tribo charge maps. Everything little endian.

Offset 0 magic TRCH four ascii bytes.
Offset 4 version uint32.
Offset 8 dtype code uint32. 2 means int16 pixels 16 means float32 pixels.
Offset 12 two uint32 nx ny pixel counts per axis.
Offset 20 two float32 sx sy mm per pixel per axis. These change per file and must be read.
Offset 28 uint32 data offset where pixels start. You must use this offset field; do not assume 64.
After offset nx times ny values in announced dtype x fastest so index for x y is x plus nx times y.

Each map contains one main triboelectric patch that is elongated along draw direction long axis along x and it is the only patch that counts plus some round static dot artefacts that are near circular and must be ignored. You can tell them apart by shape: elongated if longest at least 10 voxels and more than 1.6 times shortest, round otherwise. Also one to three tiny dust specks must be ignored — most are far away, but one config has a speck within the halo that must still be excluded by not growing into it. Keep only main elongated patch using 8 neighbour connectivity plus shape filtering.

Calibration lab shows each square mm of charged patch holds 1.5 nC. So charge in nC equals patch area mm2 times 1.5. Area itself must be recovered despite blur.

Threshold counting cannot be precise. Low cutoff includes halo and overcounts, high cutoff misses feathered edges and undercounts. No single fixed relative cutoff works across files because brightness, blur width, gradient and spacing change.

Blur preserves total signal but not apparent size, so naive threshold counts are biased in ways that depend on blur and brightness and do not generalise. Recovering true charge requires handling background, noise, blur, and shape discrimination robustly. Grading at two percent tolerance demands a physically grounded recovery, not a fixed cutoff.

Implementation constraints parse bytes yourself using only standard library. Allowed stdlib modules include struct sys math random tempfile re and the rest of the stdlib is allowed — array, collections, bisect, statistics are permitted. The following are banned and will be rejected by test from scratch: numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath pty plus any array imaging or graph helper library. Banned calls include eval exec compile __import__ chr. Banned dunder attributes include __subclasses__ __builtins__ __code__ __globals__ __getattribute__. Banned runtime tricks include subprocess os system popen exec fork walk listdir scandir open importlib runpy ctypes filesystem listing and any obfuscation that hides paths using chr bytes fromhex b64decode bytearray bytes tricks or string concatenation that builds forbidden paths. Do not attempt to open or list the tests directory and do not reference test_outputs heldout reference_charge _gen GEOM_TRUTH or geometric_truth in your solver source. Your solver must work on random temporary files not hardcoded paths.

Print charge in nC as last word.
