I run the fuel cell test stand in our energy lab. We have this Nafion membrane that sometimes forms a tiny blister during hot press. When the blister lets go, the anode pressure spikes for a moment and then tails off slowly because our sensor amp is slow. Meanwhile the whole stack is heating up so the baseline creeps upward and the coolant pump makes little shivers in the trace that look like real events. My boss wants the true burst size in kilopascals for the big pop, not the shivers, so we can grade delam severity.

Please write a small script at /app/solve.py. We call it like python at /app/solve.py with a file path and we look at the last word you print. That last word should be the real blister pressure in kPa for the main pop.

I left you a sample at /app/data/scene.fmbp you can open locally. The hidden evaluation uses other files with different burst sizes, creep rates, sensor gains, and vibration patterns you never saw. If you hardcode the sample number you will fail hidden.

The file type I invented is called FMBP. All values are little endian. Here is how I laid it out:

It starts with four bytes ascii FMBP.
Then four bytes version uint32 which is 1.
Then four bytes total sample count N uint32.
Then four bytes data offset uint32 where pressure samples begin.
Then four bytes interval float32 seconds per sample, e.g. 0.0008.
Then four bytes gain float32 trim factor.
Then four bytes baseline floor uint32 hint, ignore it, real baseline drifts.
The header is at least 28 bytes long and may have junk padding between 28 and data offset. Use the data offset field from header, do not assume 64. My hidden files use 32 40 64 96 128.
After data offset comes N int16 little endian numbers. Each number is pressure times ten, so real pressure equals value divided by ten kPa.

What is inside each trace: a gentle upward creep from heating, plus a little random noise, plus one big pop where pressure shoots up and has long low tails from amplifier smear, plus two to five tiny far spikes from pump shiver, plus one broad low hump from table rumble. That broad hump is wide and has many samples above threshold but its total pressure is small, so if you choose event by how many samples it has you will pick the wrong one. The real blister is the one with big charge mass, not big count.

Why a simple cutoff does not work for me: if I set cutoff low I include halo plus broad hump and I get 60 to 90 percent too high, if I set cutoff high I cut off low tails that still carry pressure and I get 30 to 55 percent too low. No single fixed cutoff works because gain and baseline change per membrane and per batch. The smear keeps total pressure. True pressure comes from ideal occupancy before blur, using interval and gain to get kPa. Only main pop counts, broad hump and far spikes do not. So true pressure equals sample count of main pop before blur times plateau times interval times gain over ten for deci conversion. Even though smeared peak looks low and wide, area is preserved, so you can recover via sum of background corrected signal over main plus halo divided by plateau times interval times gain over ten.

We check within three percent relative, only precise method passes.

Coding rules: parse bytes yourself with struct. You may use struct, sys, math, random, tempfile, re, collections. You may not use numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty, importlib, runpy, ctypes. No eval, exec, compile, __import__, chr. No tricks like subprocess, os system, os popen, os exec, os walk, os listdir, os scandir, os open, pty, importlib, runpy, or hiding paths via chr, bytes fromhex, base64, b64decode, bytearray, or building paths by concatenation. Do not try to open or list /tests and do not mention test outputs, heldout, reference volume, _gen, geometric truth in your code. Your solver must work on random temp files, not hardcoded paths.

At the end print pressure kPa as last word float. Traces are a few thousand samples long, recursion will overflow, use iterative loops.

Thank you for helping the fuel cell team, this blister grading is important for stack yield.
