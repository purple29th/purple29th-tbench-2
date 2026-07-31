I work in the fab on EUV plasma chambers that etch metal layers. After plasma clean, charge stays trapped on the chamber wall and slowly leaks as current on the wall probe. If too much remains the next reticle gets particle defects.

Please create a file at /app/solve.py. When we run python at /app/solve.py plus a scan file path, your program should print the true wall decay charge in microcoulombs as the last word. We grade within three percent.

I give you a sample file at /app/data/scene.euvc to try. Hidden tests use other files you never saw with different charge amounts, drift speeds, gains, and shutter patterns. Do not hardcode sample numbers. Your code must work on any path given as first argument.

My file format is called EUVC, I made it myself on the plasma controller. All numbers are little endian:

First four bytes are ascii EUVC.
Next four bytes are version uint32 value 1.
Next four bytes are total samples N uint32.
Next four bytes are data offset uint32 where wall current data starts.
Next four bytes are sample interval float32 seconds, for example 0.0007.
Next four bytes are gain float32 calibration.
Next four bytes are baseline floor uint32 hint, do not trust, real baseline drifts with wall temp.
Header is at least 28 bytes and may have random padding between 28 and data offset. You must use data offset field, do not assume 64. Hidden files use varied offsets 32 40 64 96 128.
Payload at data offset is N int16 values little endian, each is wall current in mA times 10. So divide by 10 to get mA.

Inside each file there is a slowly drifting background plus noise plus one main wall discharge where current jumps high with long tails from RF low pass smear, plus a few tiny far blips from shutter motion, plus one wide low bump from chamber vibration. The wide bump is broad and has many samples but small total charge, so picking the longest cluster by count gives wrong answer. Main event is the one with biggest total charge mass, not biggest count.

Simple cutoff fails here. Low cutoff counts halo plus wide bump and counts too much, about 60 to 88 percent high. High cutoff cuts off low tails that still carry charge and counts too little, about 28 to 52 percent low. No fixed cutoff works because gain and drift change per chamber and per lot. The blur keeps total charge. Area under smeared curve equals ideal count times plateau, so charge is conserved even though peak is lower and wider. True charge is defined as integral of ideal wall discharge before blur, in microcoulombs. Only main wall event counts, wide bump and far blips do not. For ideal occupancy, charge equals number of main samples times plateau deci mA divided by 10 times interval seconds times gain times 1000. Because blur conserves total charge, sum of smeared residual equals sum of ideal, you can recover charge by integrating background subtracted signal over main plus its halo: charge uC equals sum residual over main plus halo divided by 10 times interval times gain times 1000.

Grading is at three percent tolerance, only a genuine precise method passes.

Implementation rules: parse bytes yourself with struct only. Allowed modules struct, sys, math, random, tempfile, re, collections. Banned modules numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty, importlib, runpy, ctypes. Banned calls eval, exec, compile, __import__, chr. Banned tricks subprocess, os system, os popen, os exec, os fork, os walk, os listdir, os scandir, os open, pty, importlib, runpy, plus any obfuscation that hides paths via chr, bytes fromhex, base64, b64decode, bytearray, etc. Do not open or list /tests directory and do not mention test outputs, heldout, reference volume, _gen, geometric truth in your solver.

Print charge as last word float.

Thanks for helping the EUV team, this is needed for defect control.
