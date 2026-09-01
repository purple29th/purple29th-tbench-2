I run a mycology field lab in a Pacific Northwest evergreen duff layer studying Armillaria ostoyae honey fungus. Its rhizomorphs glow faintly at night (foxfire, bioluminescence from luciferin). We image fresh duff slabs at midnight with a low light sCMOS that writes a custom 2D container we call mycr for mycelial cord radiance.

You must automate total illuminated cord length grading.

Please make a file at /app/solve.py. We run python /app/solve.py /tmp/input_*.mycr and take the last printed number as total bioluminescent cord length in millimeters.

There is one example at /app/data/scene.mycr for local debugging (about fifteen mm with the 0.4 mm hyphal repeat). Real grading uses entirely new maps I create at runtime with random names like input_a3f9.mycr, new dimensions, pixel pitch, thickness, brightness, blur, background, seed. Hardcoding fifteen mm from sample fails hidden.

Container spec — little endian, byte ranges:

| Bytes | Type    | Field |
|-------|---------|-------|
| 0-3   | ASCII   | `MYCR` magic |
| 4-7   | uint32  | version |
| 8-11  | uint32  | dtype id (2=int16, 16=float32) |
| 12-15 | uint32  | width |
| 16-19 | uint32  | height |
| 20-23 | float32 | sx pixel pitch mm |
| 24-27 | float32 | sy pixel pitch mm |
| 28-31 | uint32  | payload_start |
| 40-43 | float32 | post_veil_multiplier |

`payload_start` can be 48, 64, 80, 96, 128 — respect the header value. `post_veil_multiplier` is at bytes 40-43 and scales the mm result and varies 0.85–1.35 per file (sample is 1.0; hidden case offset 96 uses 1.22 and fails if ignored). Bytes between header and payload are zero padding. At `payload_start` you have `width*height` samples in the announced dtype, x fastest: index = x + width*y. `sx`, `sy`, `payload_start`, and `post_veil_multiplier` vary per slab and must be read. `payload_start` is always ≥48 so the multiplier at 40-43 never overlaps payload.

What counts. Inside duff there are glowing locations. Real foxfire rhizomorphs are ragged and stretched along grain, not circular. We also see round bacterial colonies from Bacillus that glow with similar color but are almost round and must be skipped. And we see tiny far soil dust specks in corners near 5,5 and 75,75 far from center that must be skipped. Some slabs have two distant rhizocords both along grain, both count, you must add their recovered areas before length conversion. Keeping only single biggest loses 40-50% in those slabs.

How we decide in lab. I estimate a robust duff base glow and noise, mark bioluminescence clearly above base as candidate, group with 8-connected flood in 2D, then keep fiber-stretched groups and reject compact bacterial balls and far dust by shape and integrated brightness.

Why simple cutoff fails. Low cutoff includes whole aureole from fog scattering and lens blur and roughly doubles my mm. High cutoff clips ragged hyphal tails that are dim because of partial pixel fill and loses third to half. Board has varying base, multiplier, blur width, so no fixed number works.

What saves us is photons are conserved, only spread. Sum of base-subtracted glow over rhizocord plus its faint skirt divided by true core level gives true pixel count. Then area mm2 from sx*sy, length mm as area / (hyphal repeat 0.4 mm) * multiplier. You first undo blur to get area, then convert to length.

If you nail base and core you are within a percent, we grade three percent.

Coding rules. You must parse bytes yourself, only stdlib. Allowed helpers struct sys math random tempfile re. Forbidden libs numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any imaging array graph lib. Forbidden calls eval exec compile __import__ chr ord breakpoint bytes bytearray. Forbidden tricks subprocess os system popen exec fork walk listdir scandir pty importlib runpy ctypes filesystem listing or hiding forbidden filenames with chr fromhex base64 b64decode bytearray. Do not try to open or list tests folder (the solver naturally needs to open the input file given as argv). Do not mention /tests test_outputs heldout tests/_gen GEOM_TRUTH geometric_truth reference_mass reference_length ground_truth in solver. Solver must work on any random temp path.

Print span in mm as last printed token. Example around fifteen mm with the stated 0.4 mm repeat.

This task is intentionally unique and not tied to elements — it is forest mycology bioluminescence, total illuminated hyphal length, with embedded payload_start and gain fix that must be read from header. Ignoring either fails hidden cases at offset 96 and 128.
