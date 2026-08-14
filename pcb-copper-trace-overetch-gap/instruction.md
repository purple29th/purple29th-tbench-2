Ni-P pit area from WLI – automotive connector

Situation: copper connector pins get electroless nickel-phosphorus, ~12 µm. During plating hydrogen bubbles stick, leaving a micro pit to Cu. Salt spray shows red rust, part fails.

Metrology: white-light interferometer (Bruker). Airy disk and stage vibration smear deep pit into broad shallow cloud; true shape is compact but image is wide faint dish. Need true area mm2, not cloud extent.

Run: /app/solve.py <file>.enpp prints area as last token. Example at /app/data/scene.enpp for dev; hidden eval uses different files each run with per-run jittered dims, spacing, gain, blur, tilt, noise and positions from random seed, plus one fully random extra scene. No memorization.

File ENPP: little-endian binary, header: magic ENPP 4B, version, dtype (2=int16,16=float32), dimensions nx ny, spacing sx sy mm per pixel anisotropic, offset, then nx*ny values x fastest (x+nx*y). Bright = pit.

One main pit scored per file: roughly round with two faint side lips where bubble pinned – lips count. Distractors: 1-2 distant dust specks (bright compact) and a distant shallow scratch (many pixels dim) – ignore, main dominates integrated brightness; counting pixels fails on scratch.

Naive threshold fails: low keeps halo ~2x area, high loses lips ~0.5x. Gain/blur/tilt/noise shift, so no fixed level works.

Accuracy 3% relative.

Allowed imports: struct, sys, math, random, re only. No tempfile (removed – it exposed os via _os). No numpy, scipy, imaging, graph, os, io, pathlib, socket, multiprocessing, glob, etc. No eval/exec/compile/chr/fromhex/b64decode. No os link/rename/symlink. Source must not contain substrings /tests, test_outputs, heldout, GEOM_TRUTH, geometric_truth, reference_volume anywhere. Attribute accesses like os.walk, os.system, os.listdir, os.scandir, os.rglob, os.popen, os.exec*, os.spawn*, os.fork are blocked. Plain helper named walk() is allowed.

Output mm2 e.g. 12.345.
