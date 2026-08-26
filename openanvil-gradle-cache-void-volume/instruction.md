Build OpenAnvil Gradle cache void measurer.

Context: OpenAnvil Android grader (`runtimes/android/Dockerfile`) builds React Native apps with Hermes. Gradle cache misses leave elongated void gaps along the build sweep X in the intermediate artifact layer. Lab microCT captures the void layer for QA. Reconstruction point spread smears the gap, plus detector adds offset and noise. Simple voxel counting fails across recipes.

Goal: write /app/solve.py that takes a volume path and prints total cache void in cubic millimetres. Example at /app/data/scene.anvl for local dev; hidden eval uses unseen volumes with random tmp paths, varied extents, pitches, gain, blur. Do not hardcode example numbers or paths.

Binary ANVL layout little-endian:
- bytes 0-3: ASCII ANVL
- 4-7: u32 version
- 8-11: u32 sample type 2=int16 16=float32
- 12-23: three u32 extents nx ny nz
- 24-35: three f32 pitches sx sy sz mm per voxel, per-file varying, must be parsed
- 36-39: u32 payload start
- after: nx*ny*nz samples in type order, x moves fastest: idx = x + nx*(y+ny*z)

Scene content: Gradle cache void that is elongated along X (cache miss trench) versus round duplicate-dependency bubbles that are artefacts to discard via elongation vs compactness test. Void interior brightest, edge fades due to partial volume and smear. Base offset flat plus noise. Occasional isolated bright grains far from main void are dust to ignore. Keep main elongated trench via clustering plus geometry test.

Why naive fails: low cut keeps big glow and inflates 60-100pct, high cut drops thin trench ends and deflates 25-45pct, no single cut works because gain and spread vary. Brightest voxels indicate where mass concentrated, not how many to count. Flat interior obscured by noise and blur.

Physics: point spread preserves total integrated attenuation; smear moves signal but sum conserved. So true void can be recovered from pedestal-corrected sum divided by interior level, provided main void separated from far grains, pedestal estimated without bias from void, interior level estimated robust to noise, and halo extent decided without merging bubbles.

Accuracy need 3pct relative; shortcut methods off by large margin.

Coding rules: only stdlib, no external libs. Allowed imports struct sys math re. Forbidden numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io tempfile posixpath ntpath genericpath plus imaging graph array helpers. Forbidden calls eval exec compile __import__ chr. Forbidden runtime tricks subprocess os.system popen exec walk listdir scandir open symlink link rename replace pty importlib runpy ctypes filesystem listing chr bytes base64 obfuscation building forbidden paths. Do not open or list /tests, do not mention test_outputs heldout reference_volume _gen GEOM truth. Work on arbitrary tmp file path.

Output last word is volume mm3.
