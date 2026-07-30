I run the fuel cell test rig full time. Our Nafion membrane sometimes puffs up into a tiny blister during hot press and then pops. When it pops the anode side pressure jumps and then rings for a while because our pressure amp is slow. At the same time the stack is getting hotter so the baseline wanders upward and the coolant pump shakes the whole table and makes little wiggles that look like real pops. My lead wants the real size of the big pop in kilopascals, not the wiggles.

Please write a file at /app/solve.py. We run it like python at /app/solve.py with a scan file path, and your last printed word should be the true blister size in kPa.

I left a sample at /app/data/scene.blpr for local try. Sample true pressure is about 4.9 to 5.0 kPa within three percent. Hidden evaluation uses other files with different pop sizes, wander rates, sensor gains, and shiver patterns you never saw. Do not hardcode sample numbers.

My file type I call BLPR, all little endian:

It starts with four bytes ascii BLPR.
Then four bytes version uint32 1.
Then four bytes total samples N uint32.
Then four bytes data offset uint32 where samples start.
Then four bytes sample period float32 seconds per sample.
Then four bytes gain float32.
Then four bytes baseline hint uint32, you can ignore, real baseline wanders.
Header is at least 28 bytes and may have junk between 28 and data offset. You must use data offset field, not assume 64. Hidden uses 32 48 72 96 128.
After data offset comes N float32 little endian pressure values in kPa.

Inside each trace there is gentle upward wander from heating plus hiss plus one big pop that shoots high and has long low tails from amp smear, plus a couple tiny far spikes from pump shiver, plus one broad low hump from table rumble. That hump is wide and has many points above threshold but its total pressure is tiny, so choosing event by point count gives wrong answer. The true blister is the one with biggest area mass, not biggest count.

A simple cutoff fails. Low cutoff keeps halo plus hump and reads way too high, roughly 70 to 100 percent high. High cutoff chops low tails that still carry pressure and reads too low, roughly 35 to 60 percent low. No single cutoff works because gain and wander change per lot and per membrane. The smear keeps total pressure. True pressure is sum of baseline corrected signal over main pop plus halo times interval times gain. Only main pop counts, broad hump and far spikes do not. Because smear conserves area, total residual over main plus halo times interval times gain equals true pressure. No plateau division is needed for this format since payload is already in kPa and residual already includes plateau.

We check within three percent relative, only precise method passes.

Coding rules: parse bytes yourself with struct only. Allowed modules struct, sys, math, random, tempfile, re, collections. Banned modules numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, shutil, io, os, pty, importlib, runpy, ctypes. Banned calls eval, exec, compile, __import__, getattr, setattr, hasattr, globals, locals, vars, dir, chr, ord, breakpoint, base64, binascii, codecs. Banned tricks subprocess, os system, os popen, os exec, os walk, os listdir, os scandir, os open, pty, importlib, runpy, plus hiding paths via chr, bytes fromhex, base64, b64decode, bytearray. Do not open or list /tests and do not mention test outputs, heldout, reference volume, _gen, geometric truth in your solver. Work on random temp files, not hardcoded paths.

Print pressure kPa as last word float. Traces are a few thousand samples, recursion will overflow, use iterative.

Thanks for helping the fuel cell team.
