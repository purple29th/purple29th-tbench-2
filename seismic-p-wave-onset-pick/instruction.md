hey I am doing hammer seismic crew this summer and I just started logging traces myself. we have one geophone vertical channel per shot and my lead asked me to build quick tooling to pick P arrival but I am stuck with S being bigger.

we dump each trace via my tiny custom binary SEIS little endian I wrote from kotlin ByteBuffer FileOutputStream. its not standard segy, just a small format that works on my field laptop.

your job is write /app/solve.py that reads path as first arg. I will run python3 /app/solve.py /path/to/trace.seis and I need last token of stdout to be integer sample index where P wave first starts. that is what I actually need for my crew to compute hammer timing.

you can try sample at /app/data/trace.seis locally. I have other hidden files you never saw with different lengths dt baseline P S amps spike noise and S P gap so dont hardcode my sample.

SEIS format is super simple I made.

first four bytes ascii SEIS magic I check that
next four bytes u32 version 1 or 2 may vary I bumped it once so you must read it
next four bytes u32 data offset varies 64 to around 128 because I have padding you must read it and seek do not hardcode 64 or you will read zeros
next four bytes u32 n samples total
next four bytes f32 dt seconds per sample this changes every file cause I change samplerate in field so read it
next four bytes f32 baseline maybe around 0 but drifts
next four bytes two u32 reserved header at least 32 bytes plus padding respect data offset

payload at offset is n int16 little endian amplitude values. index is time.

what is inside: I see one P arrival early where ground first moves small wiggle then later bigger S arrival plus random short spikes from trucks and generators plus flat background plus sensor hiss. P is smaller than S so if you just pick max amplitude you get S wrong. Spike may be brighter than P but only 1 sample so short. S P gap changes. Some of my traces have P super early near sample 80 cause I triggered late.

how I defined true: first sample where P energy starts rising from background before peak. my generator saves that index as truth.

why my first threshold try failed: I set fixed amplitude threshold and it grabbed S first or grabbed spike and gave huge index. No fixed threshold works across files because gain and dt change and S is always larger.

what finally worked for me: I had to estimate background from early quiet window like first 50 samples not whole trace, get noise via median absolute deviation, then look for energy rise using short term over long term average ratio and require sustained rise not one spike, and I had to use dt to convert my time windows to samples so hardcoding sample counts fails when I change dt from 0.001 to 0.004.

sample trace.seis has P around few hundred. grading tolerance is +- max 5 samples so small error ok.

parse binary yourself using only struct. banned are numpy scipy obspy pandas torch tensorflow sklearn skimage cv2 PIL pillow networkx igraph imageio glob pathlib shutil io os. also banned tricks like subprocess os system popen exec and dunder builtins dict subclasses mro and importlib runpy ctypes eval exec compile and getattr setattr hasattr globals locals vars dir chr ord base64 etc. do not open tests directory or heldout files.

at end print integer index as last token. I compare last int against truth.

files are few thousand samples 1000 to 4000 so use loop not recursion.

this will help my crew get timing right.

