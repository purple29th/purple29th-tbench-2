Fix gap volume estimator in PCB copper trace overetch inspection

Inspiration
This comes from battery coulomb counting where you integrate current to get charge despite baseline and spike artifacts. Blur spreads energy but conserves total, so true volume can be recovered from geometric occupancy. Similar to ultrasonic delam tasks and pcb undercut gap tasks and sintered silver void tasks and nickel pit tasks.

Context
I work on factory line inspecting copper trace overetch gaps. After etching, overetch creates a small gap under solder mask that hurts reliability. We use X ray to see it but X ray blur spreads the gap signal everywhere, so the gap looks larger and fuzzier than its true size.

File to fix is /app/solve.py invoked as python /app/solve.py <scan_path> and the last word printed will be taken as the gap volume in mm3. You are provided one example scan for local testing at /app/data/scene.pcb. You may read this file while developing, but hidden grading uses different scans you have never seen, with different dimensions, spacings, brightness, copper thickness, and voxel pitch, passed as random temporary files. Do not hardcode numbers or paths from the example. Your solver must work on any file path given as the first argument. Hardcoding the sample volume will fail the hidden volume checks.

Format pcb is a custom binary for X ray overetch gap volumes. Everything is little endian:
* Offset 0: magic PCBG four ASCII bytes.
* Offset 4: version uint32.
* Offset 8: dtype code uint32. 2 means int16 voxels, 16 means float32 voxels.
* Offset 12: three uint32 values for voxel counts per axis, nx, ny, nz.
* Offset 24: three float32 values for millimetres per voxel per axis, sx, sy, sz. These change per file and must be read from the header.
* Offset 36: uint32 data offset where voxel values start.
* After data offset: nx times ny times nz values in the announced dtype, x fastest, so linear index for x y z is x plus nx times (y plus ny times z).

Trace generation is hidden in tests but roughly one main elongated gap that is the only gap that counts, plus round solder voids that are artefacts and must be ignored. You can tell them apart by shape, elongated versus round. The centre of each gap is flat and bright where X ray sees open gap, the border is dimmer with partial fill smeared by X ray blur. There is a flat ambient background plus sensor noise. Some scans also have one or two tiny bright specks far away from dust artefacts that must be ignored. Keep only the main elongated gaps using 26 neighbour connectivity plus shape filtering.

Flat core 45 to 60 voxels occupancy 1.0, left feather 6 to 12 voxels occupancy 0.3 times one minus normalized distance, right tail 16 to 22 voxels occupancy 0.4 times one minus normalized distance. Amplitude amp few hundred. Baseline is constant offset bg plus Gaussian noise. Gaussian blur sigma a few points is applied to clean volume including specks to simulate spreading, but it conserves sum. That is the hard part.

Spikes are 1 to 3 narrow transients width a few voxels amplitude about 0.9 times amp with triangular falloff. Spikes may appear far from gap as isolated speck and must be ignored, or may overlap feather tail or even core and still must be excluded otherwise volume overcounts by a few percent. True volume is defined only from geometric occupancy sum true occ times amp times sx sy sz and excludes spikes entirely. Tests compute truth at runtime from fixed random seeds, so no fixtures to read.

Bug
Current implementation estimates background as mean which is biased, uses fixed threshold 50, picks largest component by count not mass, uses max as plateau which is noise sensitive, and integrates as count times plateau times sx sy sz with no tail inclusion and no spike suppression. It overcounts background and spikes and undercounts tails.

Threshold counting cannot be precise. A low cutoff includes a huge halo and overcounts by eighty to one hundred thirty percent. A high cutoff misses thin overetch that never gets bright enough and undercounts by thirty to fifty percent. No fixed cutoff works across files because brightness and blur width change. The blurry images give the best clue where signal is most concentrated, not how many bright voxels there are. The true core is flat but hidden by blur noise.

The blur spreads energy but does not create or destroy signal. That physics makes precise volume recovery possible despite smear, but using it requires separating the main gap from far specks, estimating background without bias from the gap itself, estimating the true concentrated intensity without being fooled by noise, and deciding how far the faint halo extends without merging specks.

The optics apply normalized blur that preserves total power; image just spread out. Background pedestal and random noise vary per shot. Buggy code estimates background as mean of whole frame biased upward by gap, uses fixed threshold, picks largest region by pixel count, and uses count times max. That misses faint tail and halo and keeps voids.

An offshore platform flares excess hydrocarbon and monitors it with fixed IR radiometer for emissions accounting. A data center monitors 48V copper busbars with magneto-optical imager. A factory inspects electroless nickel-phosphorus pits and sintered silver die attach voids with X ray and WLI. All share same underlying physics: Gaussian blur conserves integral, so total energy preserved but spread into halo that looks larger and fuzzier. Simple threshold counting fails: low cutoff includes huge halo and overcounts by eighty to one hundred thirty percent, high cutoff misses thin gaps and undercounts by thirty to fifty percent. No fixed cutoff works across files because brightness and blur width change.

Simple shortcuts are off by a large margin. Grading is at three percent tolerance, only a genuine precise method passes. Accuracy 3% relative.

Implementation constraints: parse bytes yourself using only the standard library. Allowed stdlib modules include struct, sys, math, random, tempfile, re. The following are banned and will be rejected by test from scratch: numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, socket, multiprocessing, glob, pathlib, os, io, posixpath, ntpath, genericpath, plus any array, imaging, or graph helper library. Banned calls include eval, exec, compile, __import__, chr. Banned runtime tricks include subprocess, os system, os popen, os exec, os fork, os walk, os listdir, os scandir, os open, pty, importlib, runpy, ctypes, filesystem listing, and any obfuscation that hides paths using chr, bytes fromhex, base64, b64decode, bytearray, bytes tricks, or string concatenation that builds forbidden paths. Do not attempt to open or list the /tests directory, and do not reference test outputs, heldout, reference volume, _gen, GEOM TRUTH, or geometric truth in your solver source. Your solver must work on random temporary files, not hardcoded paths.

Expected
Fix the estimator to be robust without hardcoding positions gains or seeds. It should handle baseline that is not biased by gap, handle noise, include thin feather and tail as part of true volume, exclude narrow spikes even when they overlap the gap, and recover volume using conservation. Empty or all zero input should return near zero. Grading checks relative error within three percent. Tests include random seeds plus heavy spike case plus global fails where a spike sits in the tail plus threshold fails. Two guard tests ensure naive global mass and simple count threshold both fail. All tests must pass.

Verification
Run pytest tests/test_outputs.py -v from repo root with PYTHONPATH set to include src. Print the volume in mm3 as the last word on stdout.

