I work in our energy lab testing fuel cell membranes. The membrane can develop a small blister that lifts and blocks gas flow. When the blister pops it releases a burst of pressure that we log with a pressure sensor. The sensor amplifier low pass smears the burst plus we get baseline drift from stack heating and random blips from coolant pump vibration. I need to know the true blister pressure that was released, because that tells us how severe the delamination is.

Please create a file at /app/solve.py. When we run python at /app/solve.py plus a scan file path, your program should print the true blister pressure in kilopascals as the last word. We grade within three percent.

I give you a sample file at /app/data/scene.fmbp to try. Hidden tests use other files you never saw with different pressure amounts, drift speeds, gains, and vibration patterns. Do not hardcode sample numbers. Your code must work on any path given as first argument.

My file format is called FMBP, I made it myself in the lab tool. All numbers are little endian:

First four bytes are ascii FMBP.
Next four bytes are version uint32 value 1.
Next four bytes are total samples N uint32.
Next four bytes are data offset uint32 where pressure data starts.
Next four bytes are sample interval float32 seconds, for example 0.0008.
Next four bytes are gain float32 trim.
Next four bytes are baseline floor uint32 hint, do not trust, real baseline drifts with heater.
Header is at least 28 bytes and may have random padding between 28 and data offset. You must use data offset field, do not assume 64. Hidden files use varied offsets 32 40 64 96 128.
Payload at data offset is N int16 values little endian, each is pressure in kPa times 10. So divide by 10 to get kPa.

Inside each file there is a slowly drifting background plus noise plus one main blister where pressure jumps high with long tails from low pass smear, plus a few tiny far blips from pump shake, plus one wide low bump from table vibration. The wide bump is broad and has many samples but small total pressure, so picking the longest cluster by count gives wrong answer. Main event is the one with biggest total pressure mass, not biggest count.

Simple cutoff fails here. Low cutoff counts halo plus wide bump and counts too much, about 60 to 90 percent high. High cutoff cuts off low tails that still carry pressure and counts too little, about 30 to 55 percent low. No fixed cutoff works because gain and drift change per membrane and per lot. The blur keeps total pressure. Area under smeared curve equals ideal count times plateau, so pressure is conserved even though peak is lower and wider. True pressure is defined as integral of ideal occupancy before blur, using interval and gain to convert to kilopascals. Only main blister counts, wide bump and far blips do not. True pressure equals number of samples that belong to main blister before blur times plateau times interval times gain divided by 10 conversion for deci kPa. Because blur conserves total pressure, you can recover it via total background subtracted signal divided by true plateau intensity times interval times gain divided by 10.

Grading is at three percent tolerance, only a genuine precise method passes.

Implementation rules: parse bytes yourself with struct only. Allowed modules struct, sys, math, random, tempfile, re, collections. Banned modules numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty, importlib, runpy, ctypes. Banned calls eval, exec, compile, __import__, chr. Banned tricks subprocess, os system, os popen, os exec, os fork, os walk, os listdir, os scandir, os open, pty, importlib, runpy, plus any obfuscation that hides paths via chr, bytes fromhex, base64, b64decode, bytearray, etc. Do not open or list /tests directory and do not mention test outputs, heldout, reference volume, _gen, geometric truth in your solver.

Print pressure as last word float.

Thanks for helping the fuel cell team, this is needed for blister severity.
