hey i am on a research vessel mapping hydrothermal vents with multibeam sonar. vents puff hot mineral rich water full of micro bubbles that show up as bright acoustic plumes, but water column scattering plus the sonar beam pattern smears the plume all over, so it looks much bigger and fuzzier than it really is.

i need a program that tells the true physical size of the vent plume in cubic mm, not the smeared acoustic cloud. precision matters for estimating heat flux.

make file named solve.py inside app folder. we call it as python app solve.py with scan path as argument. last word printed is taken as volume.

you get one example to try named scene.svol inside data folder that is inside app folder. you may read that file while developing, but hidden grading uses different scans you have never seen that vary in grid size, voxel pitch, bubble density, seawater background, and sonar blur, passed as random temporary files. do not hardcode numbers or paths from example.

what is svol. our own small binary for sonar vent plume volumes. everything little endian.

file starts with four ascii S V O L.

version is next four bytes unsigned thirty two little endian.

dtype code next four bytes unsigned thirty two little endian. code 2 means int16 voxels, code 16 means float32 voxels.

next twelve bytes are three unsigned thirty two counts of voxels per axis, historically nx, ny, nz.

next twelve bytes are three float32 values for mm per voxel per axis, historically sx, sy, sz. they change per file so you must read them from header.

next four bytes unsigned data offset where voxel data starts.

after data offset you have nx times ny times nz values in the announced dtype, x fastest, so index for x,y,z is x plus nx times (y plus ny times z).

inside is one solid plume where bubbles are dense. centre is flat bright where acoustic backscatter saturates. border is dimmer with partial fill smeared by scattering and beam pattern. flat seawater background plus sonar noise. some scans have one or two tiny bright specks far away from fish or debris, ignore them and keep only the main connected plume using twenty six neighbours.

this is tricky and every agent finds it hard to be precise. bright voxel counting is never precise. a permissive cutoff includes the huge faint halo and inflates a lot, a strict cutoff misses thin tendrils that never get bright enough and deflates a lot. no fixed cutoff works across files because bubble density, seawater level, and diffusion width change per scan. counting dark pixels is not the clue, the overall energy pattern is.

the sonar spreads acoustic energy but total backscatter is preserved, which makes subvoxel recovery possible despite the smear. using it requires separating main plume from far specks, estimating seawater background without bias from plume itself, estimating the true interior level despite noise, and deciding how far the faint halo goes without merging distant specks. that combination is hard and where most shortcuts fail.

simple heuristics are far outside tolerance. grading uses three percent relative tolerance, only careful reconstruction meets it.

implementation rules: parse bytes yourself with only standard library. allowed modules include struct, sys, math, random, tempfile, re. the following are banned and checked in test_from_scratch: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, os, io, posixpath, ntpath, genericpath. banned calls include eval, exec, compile, __import__, chr. also forbidden are runtime tricks like subprocess, os.system, os.popen, filesystem listing via walk, listdir, scandir, rglob, glob(), and path hiding via chr(), bytes.fromhex, base64, b64decode, bytearray, bytes([...]) patterns, or string concatenation building forbidden paths. do not try to open or list /tests and do not reference test_outputs, heldout, reference, _gen, GEOM_TRUTH, geometric_truth, reference_volume in your solver source. solver must work on random temporary files, not hardcoded locations.

print volume mm3 as last token.
