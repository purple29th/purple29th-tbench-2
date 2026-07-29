I have some custom binary volumes with extension .oncr. Each file stores a 3D scan where one solid region glows bright due to dead cell staining. The centre is flat and bright where signal saturates, the border is dimmer with partial fill smeared by scattering and PSF. There is flat ambient background plus noise. Some files have one to three tiny bright specks far away that must be ignored. I need the true physical volume of the main glowing region in cubic micrometers, not the smeared blob. My current threshold counts are way off so I need something more precise.

Make file `/app/solve.py`. We run `python /app/solve.py <scan_path>` and take the last word printed as the volume.

You get one example scan at `/app/data/scene.oncr` for local testing. Hidden grading uses other scans you never saw with different dimensions, voxel pitch, brightness, scattering strength and background. Do not hardcode numbers from the example. Your solver must work on any file path given as first arg.

Format .oncr is little endian.

* offset 0 magic `ONCR` four ASCII bytes.
* offset 4 version uint32.
* offset 8 dtype code uint32. 2 means int16 voxels, 16 means float32 voxels.
* offset 12 three uint32 counts per axis nx ny nz.
* offset 24 three float32 micrometers per voxel per axis sx sy sz. Must be read from header, changes per file.
* offset 36 uint32 data offset where voxel values start.
* after data offset nx times ny times nz values in announced dtype, x fastest, index is `x + nx * (y + ny * z)`.

Each volume contains one main solid core. Keep only main connected mass using 26 neighbour connectivity, drop far specks.

Threshold counting fails. Low cutoff includes huge halo and overcounts by eighty to one hundred thirty percent. High cutoff misses thin finger like extensions that never get bright enough and undercounts by thirty to fifty percent. No fixed cutoff works across files because brightness, clarity, scattering width and background change. Blur spreads photons but does not create or destroy energy. That physics allows precise recovery if you separate main core from specks, estimate background without bias from core, estimate true saturated level without being fooled by noise, and decide how far faint halo extends without merging specks. That is the hard part.

Grading at three percent tolerance. Only precise method passes.

Implementation constraints. Parse bytes yourself using only standard library. Allowed modules struct sys math random tempfile re. Banned modules numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath plus any array imaging or graph helper. Banned calls eval exec compile __import__ chr. Banned runtime tricks subprocess os.system os.popen os.exec os.fork os.walk os.listdir os.scandir os.open pty importlib runpy ctypes filesystem listing and any obfuscation that hides paths using chr() bytes.fromhex base64 b64decode bytearray bytes tricks or string concatenation that builds forbidden paths. Do not attempt to open or list /tests directory and do not reference test_outputs heldout reference_volume _gen GEOM_TRUTH or geometric_truth in solver source. Solver must work on random temporary files, not hardcoded paths.

Print volume in cubic micrometers as last word on stdout.
