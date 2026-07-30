I work in the semiconductor fab handling electrostatic chucks that hold wafers. After we dechuck the wafer there is residual charge that stays in the chuck. It shows as a current spike that drains slowly. The driver low pass smears it plus we get baseline drift from heater temperature and random blips from robot vibration when the arm moves. I need to know the true residual charge that got released, because that tells us if the wafer will stick next time.

Please build a small tool for me. Create a file at /app/solve.py. It will be invoked as python at /app/solve.py plus a scan path and the last word it prints will be taken as the true residual charge in microcoulombs for the main discharge event after you clean up drift and ignore far blips.

You are provided one example scan for local testing at /app/data/scene.esca. You may read this file while developing, but hidden grading uses different scans you have never seen, with different charge amounts, chuck resistances, drift rates, gains, noise, and blips including a wide low amplitude vibration that has more samples than the main event but less total charge. Do not hardcode numbers or paths from the example. Your solver must work on any file path given as the first argument. Hardcoding the sample volume will fail hidden checks.

Format esca is a custom binary for chuck residual charge. Everything is little endian:

* Offset 0: magic ESCA four ASCII bytes.
* Offset 4: version uint32 value 1.
* Offset 8: event count N uint32 total samples.
* Offset 12: data offset uint32 where payload starts.
* Offset 16: sample interval float32 seconds like 0.0008 sec.
* Offset 20: gain float32 factory trim.
* Offset 24: baseline floor uint32 just a hint, do not trust it as truth, real baseline drifts.
* Header at least 28 bytes, may have garbage padding between 28 and data offset, you must respect data offset field, do not hardcode 64. Hidden tests use varied offsets 32 40 64 96 128.
* Payload at offset is N int16 little endian values, each is real chuck current in mA times 10. So divide by 10 to get mA.

Each volume contains slowly drifting background baseline plus gaussian noise plus one main discharge event where current jumps high with long thin tails from driver low pass smear, plus 2 to 5 tiny blips far from main from robot shake, plus one wide low amplitude shake that is broad but shallow. It has larger sample count than main but smaller integrated charge, so if you pick cluster by sample count you will pick wrong one. The main event is the one that actually carries the dominant charge, not merely the longest.

Simple counting cannot be precise. A low cutoff includes halo and wide shake and overcounts by sixty to ninety percent, high cutoff misses low amplitude tails that still hold significant charge and undercounts by thirty to fifty five percent. No fixed cutoff works across files because gain and baseline and temperature drift change per batch and per chuck. The smear is charge conserving. Total charge under blurred curve equals ideal occupancy times plateau, so total area is preserved even though peak is smeared lower and wider. The true charge is defined as integral of the ideal occupancy before blur. Only main discharge counts toward this truth, wide shallow shake and far blips do not. True charge equals number of samples that belong to main discharge before blur times plateau times interval times gain times 1000 microcoulombs conversion. Because blur conserves total charge, you can recover it via total background subtracted signal divided by true plateau intensity times interval times gain times 1000.

Grading is at three percent tolerance, only a genuine precise method passes.

Implementation constraints: parse bytes yourself using only the standard library. Allowed stdlib modules include struct, sys, math, random, tempfile, re, collections. The following are banned and will be rejected by test from scratch: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, os, io, posixpath, ntpath, genericpath, plus any array, imaging, or graph helper library. Banned calls include eval, exec, compile, __import__, chr. Banned runtime tricks include subprocess, os system, os popen, os exec, os fork, os walk, os listdir, os scandir, os open, pty, importlib, runpy, ctypes, filesystem listing, and any obfuscation that hides paths using chr, bytes fromhex, base64, b64decode, bytearray, bytes tricks, or string concatenation that builds forbidden paths. Do not attempt to open or list the /tests directory, and do not reference test outputs, heldout, reference volume, _gen, GEOM TRUTH, or geometric truth in your solver source. Your solver must work on random temporary files, not hardcoded paths.

Print the charge in microcoulombs as last word on stdout. Logs are a few thousand samples, recursion will overflow, use iterative.

Thanks a lot for helping with the chuck team.
