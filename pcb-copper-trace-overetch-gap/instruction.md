Measuring copper trace over-etch clearance from PCB transmission imaging.

You work in a PCB failure laboratory checking traces that were over-etched. Excess etchant removes copper sideways forming lateral breaks that increase impedance and can open the net. This defect reduces yield and must be sized. Transmission imaging shows open clearance as bright, but the imaging forms a broad bloom that confounds simple voxel counting.

Make `/app/solve.py` executable as:

```bash
python3 /app/solve.py /path/to/cap.pcb
```

Print the sum of all clearance break volumes in mm3 as the final token of stdout. The development sample is at `/app/data/scene.pcb`. You may inspect it while coding, but secret grading uses unseen volumes with varied extents, voxel pitches, gains, and etch strengths, delivered as random temporary paths each collection. Do not hardcode sample numbers or paths.

This comes from battery coulomb counting where you integrate current to get charge despite baseline and spike artifacts. Blur spreads energy but conserves total, so true volume can be recovered from geometric occupancy. Similar to ultrasonic delamination tasks and coulomb drift charge recovery tasks and flare stack thermal energy recovery and busbar current crowding recovery.

File format:
- File is little endian.
- Bytes 0-3 hold identifier `PCBG`.
- Byte 4 holds version as UINT32.
- Byte 8 holds type as UINT32: 2 means int16 samples, 16 means float32 samples.
- Bytes 12..23 hold size as UINT32 x3 for X, Y, Z voxel counts.
- Bytes 24..35 hold step as FLOAT32 x3 for mm per voxel; these vary per file so parse them.
- Bytes 36..39 hold payload pointer as UINT32 to voxel array start.
- Then nx*ny*nz entries in declared type, X stride 1, offset = X + NX*(Y + NY*Z). No padding beyond pointer.

Inside each scan there are one or more long slim clearance breaks extended along one axis and thin along the others; all breaks that pass the slenderness filter count and their volumes sum. There are also compact round copper leftovers or solder balls that are junk and must be skipped. Separate by slenderness: break is high aspect, junk is low aspect near cubic. The centre of each break glows where imaging sees air, with uniform core, rim darker due to partial etch and imaging spread. There is uniform base level plus detector jitter. Some scans have one to three detached bright beads far from break from debris that must be ignored. Keep all dominant high aspect breaks using full volumetric adjacency plus aspect filtering and sum their volumes. This fixes the previous single-break wording that contradicted heldout_1 which contains two true boxes.

Plain bright voxel counting fails. Low threshold retains enormous spill skirts and inflates by eighty to one hundred thirty percent. High threshold drops thin clearance that never reaches high and undercounts by thirty to fifty percent. No single threshold works across runs because gain and spread differ per capture. The image indicates where flux piles up, not just bright count. Core is flat but hidden by spread and jitter.

Imaging physics: kernel is normalized, integrated signal survives spread unchanged. Sum stays constant though smeared into skirt. That preservation allows exact sizing despite bloom, but it demands detaching main breaks from remote beads, estimating pedestal without break bias, estimating core level robust to jitter, and deciding how far faint skirt spreads without merging beads.

Typical naive code mistakes: pedestal from whole volume mean biased up by break, hard fixed level, pick biggest region by count not summed flux, core from max voxel noise sensitive, integration as count times max with zero skirt and no debris cut. It miscounts base and debris and misses slim edges.

Grading checks relative error within three percent. Only true flux preservation passes. Empty scan with no breaks yields near zero volume and is now tested via empty config.

Code rules: parse bytes manually with stdlib alone. Allowed are struct, sys, math, re. Forbid numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, subprocess, importlib, runpy, ctypes, socket, multiprocessing, glob, pathlib, os, io, tempfile, posixpath, ntpath, genericpath, and any array, imaging, graph helper. Forbid calls eval, exec, compile, __import__, chr. Forbid ops system, popen, exec, spawn, fork, walk, listdir, scandir, link, symlink, rename, replace, plus introspection dunders. Do not touch /tests nor mention test_outputs, heldout, _gen, geometric_truth, reference_volume in solver. Work on random temp names, not fixed paths. Hidden suite uses distinct files each collection with per-run jittered dims and positions from a fixed master seed plus one fully random extra generated from that master seed for reproducibility.

Output the summed break clearance volume in mm3 as last word.

Local check: pytest tests/test_outputs.py -v with SOLVE_PATH pointing to your file.
