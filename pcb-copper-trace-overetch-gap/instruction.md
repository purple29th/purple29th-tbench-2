Build copper etch clearance measurer.

Context: in PCB etch line, after resist develop, alkaline etchant attacks sidewall, leaving triangular foot clearance called overetch. We capture volume with lab microCT. Reconstruction point spread smears clearance, plus detector adds offset and noise. Simple counting fails across recipes.

Goal: write /app/solve.py that takes a volume path and prints total clearance in cubic millimetres. Example at /app/data/scene.ovg for local run; hidden eval uses unseen volumes with random tmp paths, varied extents, pitches, gain, blur. Do not hardcode example numbers or paths.

Binary OVEG layout little-endian:
- bytes 0-3: ASCII OVEG
- 4-7: u32 version
- 8-11: u32 sample type 2=int16 16=float32
- 12-23: three u32 extents nx ny nz
- 24-35: three f32 pitches sx sy sz mm per voxel, per-file varying, must be parsed
- 36-39: u32 payload start
- after: nx*ny*nz samples in type order, x moves fastest: idx = x + nx*(y+ny*z)

Scene content: copper trace foot includes wedge clearance that is triangular in cross-section and long along X, versus round flux bubbles that are artefacts to discard via elongation vs compactness test. Clearance interior brightest, edge fades due to partial volume and smear. Base offset flat plus noise. Occasional isolated bright grains far from main wedge are dust to ignore. Keep main wedge via clustering plus geometry test.

Why naive fails: low cut keeps big glow and inflates 60-100pct, high cut drops thin foot and deflates 25-45pct, no single cut works because gain and spread vary. Brightest voxels indicate where mass concentrated, not how many to count. Flat interior obscured by noise and blur.

Physics: point spread preserves total integrated attenuation; smear moves signal but sum conserved. So true clearance can be recovered from pedestal-corrected sum divided by interior level, provided main wedge separated from far grains, pedestal estimated without bias from wedge, interior level estimated robust to noise, and halo extent decided without merging bubbles.

Accuracy need 3pct relative; shortcut methods off by large margin.

Coding rules: only stdlib, no external libs. Allowed imports struct sys math re. Forbidden numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io tempfile posixpath ntpath genericpath plus imaging graph array helpers. Forbidden calls eval exec compile __import__ chr. Forbidden runtime tricks subprocess os.system popen exec walk listdir scandir open symlink link rename replace pty importlib runpy ctypes filesystem listing chr bytes base64 obfuscation building forbidden paths. Do not open or list /tests, do not mention test_outputs heldout reference_volume _gen GEOM truth. Work on arbitrary tmp file path.

Output last word is volume mm3.
