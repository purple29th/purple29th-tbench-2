hey field crew logs seismic traces from hammer shots. one geophone vertical channel per file.

we dump via custom binary SEIS little endian from kotlin ByteBuffer.

your job write /app/solve.py that reads path as first arg. we run python3 /app/solve.py /path/to/trace.seis and last token of stdout must be integer sample index of P wave onset.

sample at /app/data/trace.seis you can try locally. hidden grading uses other files you never saw with different trace lengths, dt, baseline, P and S amplitudes, spike noise and S P separation. dont hardcode sample.

SEIS format is my tiny container.

first four bytes ascii SEIS magic
next four bytes u32 version 1 or 2 may vary
next four bytes u32 data offset varies 64 to around 128 due to padding you must read it and seek do not hardcode 64
next four bytes u32 n samples total count
next four bytes f32 dt seconds per sample changes every file so read it
next four bytes f32 baseline maybe around 0
next four bytes two u32 reserved but present header at least 32 bytes plus padding respect data offset

payload at offset is n int16 little endian amplitude values. x is time index.

content: one P arrival early where ground first moves plus later larger S arrival plus random short spike noise from cultural sources plus flat background plus sensor noise. P is smaller than S so picking max amplitude fails. Spike noise may be brighter than P but very short. S P separation changes. Some traces have P near edge.

true onset definition: first sample where P energy starts rising from background before peak. generator saves true index as geometric truth. blur not relevant here but energy is conserved in sense STA LTA ratio rises.

why threshold fails: fixed amplitude threshold grabs S first or grabs spike and overestimates index. no fixed threshold works across files because gain and dt change and S is larger.

real hint: you must estimate background from early quiet window, not whole trace, estimate noise via MAD, detect energy rise via short term over long term average ratio, require sustained rise not single spike, use dt to convert time windows to samples so hardcoding sample counts fails.

sample: environment/data/trace.seis has P at around few hundred. grading tolerance is +- max 2 samples and small percent of S P gap.

parse binary yourself using only struct. banned are numpy scipy obspy pandas torch tensorflow sklearn skimage cv2 PIL pillow networkx igraph imageio glob pathlib shutil io os. also banned tricks like subprocess os system popen exec and dunder builtins dict subclasses mro and importlib runpy ctypes eval exec compile and getattr setattr hasattr globals locals vars dir chr ord base64 etc. do not open tests directory or heldout files.

at end print integer index as last token. grading compares last stdout int against ground truth with tolerance.

files may have up to few thousand samples 1000 to 4000, use iterative not recursion.

good luck.
