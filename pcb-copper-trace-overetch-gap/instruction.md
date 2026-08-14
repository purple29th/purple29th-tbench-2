Measuring copper trace over-etch clearance from PCB transmission imaging.

You work in PCB failure lab checking traces that got over-etched. Excess etchant removes copper sideways forming a lateral break that lifts impedance and can open the net. This defect cuts yield and must be sized. Transmission imaging shows open clearance as bright, but the imaging forms a broad bloom that confounds simple voxel counting.

Make /app/solve.py callable as:

python3 /app/solve.py /path/to/cap.pcb

Print clearance volume in mm3 as final token of stdout. Dev sample sits at /app/data/scene.pcb. You may inspect it while coding, but secret grading uses unseen volumes with varied extents, pitches, gains, etch strength, fed as random temp paths each collection. Do not hardcode sample numbers or paths.

Container spec:

File is little endian. Bytes 0-3 hold identifier PCBG. Byte 4 holds version UINT32. Byte 8 holds type UINT32: 2 -> int16 samples, 16 -> float32 samples. Bytes 12..23 hold size UINT32 x3 for X Y Z count. Bytes 24..35 hold step FLOAT32 x3 for mm per voxel; these shift per file so parse them. Bytes 36..39 hold payload pointer UINT32 to voxel array start. Then nx*ny*nz entries in declared type, X stride 1, offset = X + NX*(Y + NY*Z). No pad beyond pointer.

Inside each scan there is a long slim clearance break extended along one axis and thin along the others; only that break counts. There are also compact round copper leftovers or solder balls that are junk and must be skipped. Separate by slenderness: break is high aspect, junk is low aspect near cubic. Break centre glows where imaging sees air, with even core, rim darker due to partial etch and imaging spread. There is uniform base level plus detector jitter. Some scans have one to three detached bright beads far from break from debris that must be ignored. Keep only dominant high aspect break using full volumetric adjacency plus aspect filter.

Plain bright voxel counting fails. Low threshold retains enormous spill skirts and inflates many tens percent. High threshold drops thin clearance that never reaches high and deflates. No single threshold works across runs because gain and spread differ per capture. The image indicates where flux piles up, not just bright count. Core is flat but hidden by spread and jitter.

Imaging physics: kernel is normalized, integrated signal survives spread unchanged. Sum stays constant though smeared into skirt. That preservation allows exact sizing despite bloom, but it demands detaching main break from remote beads, pedestal estimate excluding break bias, core level estimate robust to jitter, and decision of how far faint skirt spreads without merging beads. That is the crux.

Typical naive code mistakes: pedestal from whole volume mean biased up by break, hard fixed level, pick biggest region by count not summed flux, core from max voxel noise sensitive, integration as count*max with zero skirt and no debris cut. It miscounts base and debris and misses slim edges, error large.

Score at three percent relative. Only true flux preservation passes. Empty scan yields near zero.

Code rules: parse bytes manually with stdlib alone. Allowed are struct, sys, math, re. Forbid numpy, scipy, skimage, cv2, PIL, Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, subprocess, importlib, runpy, ctypes, socket, multiprocessing, glob, pathlib, os, io, tempfile, posixpath, ntpath, genericpath, and any array, imaging, graph helper. Forbid calls eval, exec, compile, __import__, chr. Forbid ops system, popen, exec*, spawn*, fork*, walk, listdir, scandir, link, symlink, rename, replace, plus introspection dunders. Do not touch /tests nor mention test_outputs, heldout, _gen, geometric_truth, reference_volume in solver. Work on random temp names, not fixed paths. Hidden suite uses distinct files each collection with per-run jittered dims and positions from entropy source, plus fully random extra. Retention will fail.

Output break clearance mm3 as last word.

Local: pytest tests/test_outputs.py -v with SOLVE_PATH to your file.
