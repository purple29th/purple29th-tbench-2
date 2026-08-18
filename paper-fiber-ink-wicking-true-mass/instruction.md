I work in a photo paper mill grading 120gsm rag with calendered cellulose base and kaolin clay coating applied by blade coater. We print a solid dye patch, then measure how far it feathers along fiber axis because that span tracks Cobb sizing and sheet caliper better than gravimetric mg. A UV fluorescence microscope scans it and writes a 2D container we call inkw.

Please make a file at /app/solve.py. We run python /app/solve.py /tmp/input_*.inkw and take the last printed number as span in millimeters.

There is one example at /app/data/scene.inkw for local debugging. Real grading uses entirely new maps I create at runtime with random names like input_a3f9.inkw, new dimensions, pixel pitch, thickness, brightness, blur, background, seed. Hardcoding twelve mm from sample fails hidden.

Container spec — little endian, byte ranges:

| Bytes | Type    | Field |
|-------|---------|-------|
| 0-3   | ASCII   | `INKW` magic |
| 4-7   | uint32  | version |
| 8-11  | uint32  | dtype id (2=int16, 16=float32) |
| 12-15 | uint32  | width |
| 16-19 | uint32  | height |
| 20-23 | float32 | sx pixel pitch mm |
| 24-27 | float32 | sy pixel pitch mm |
| 28-31 | uint32  | payload_start |
| 40-43 | float32 | post_coat_multiplier |

`payload_start` can be 32, 40, 48, 64, 80, 96, 128 — respect the header value. `post_coat_multiplier` scales the mm result and varies 0.85–1.35 per file (sample is 1.0; hidden case offset 96 uses 1.22 and fails if ignored). Bytes between header and payload are zero padding. At `payload_start` you have `width*height` samples in the announced dtype, x fastest: index = x + width*y. `sx`, `sy`, `payload_start`, and `post_coat_multiplier` vary per sheet and must be read.

What counts. Inside sheet there are ink locations. Real feathered wicking follows fiber and is ragged and stretched along fiber direction, not circular. We also see circular condensation beads from humidifier that are almost round and must be skipped. And we see tiny far window dust specks in corners near 5,5 and 75,75 far from center that must be skipped. Some sheets have two distant feathered blots both along fiber, both count, you must add their recovered areas before span conversion. Keeping only single biggest loses 40-50% in those sheets.

How we decide in lab. I estimate a robust paper base glow and noise, mark fluorescence clearly above base as candidate, group with connected flood, then keep fiber-stretched groups and reject compact beads and far dust by shape and integrated brightness.

Why simple cutoff fails. Low cutoff includes whole aureole from fiber scattering and lens blur and roughly doubles my mm. High cutoff clips ragged tails that are dim because of partial pixel fill and loses third to half. Board has varying base, multiplier, blur width, so no fixed number works.

What saves us is photons are conserved, only spread. Sum of base-subtracted glow over feathered blot plus its faint skirt divided by true core level gives true pixel count. Then area mm2 from sx*sy, span mm as area / (fiber repeat 0.4 mm) * multiplier. You first undo blur to get area, then convert to span.

If you nail base and core you are within a percent, we grade three percent.

Coding rules. You must parse bytes yourself, only stdlib. Allowed helpers struct sys math random tempfile re. Forbidden libs numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any imaging array graph lib. Forbidden calls eval exec compile __import__ chr ord breakpoint bytes bytearray. Forbidden tricks subprocess os system popen exec fork walk listdir scandir pty importlib runpy ctypes filesystem listing or hiding forbidden filenames with chr fromhex base64 b64decode bytearray. Do not try to open or list tests folder (the solver naturally needs to open the input file given as argv). Do not mention /tests test_outputs heldout tests/_gen GEOM_TRUTH geometric_truth reference_mass reference_length ground_truth in solver. Solver must work on any random temp path.

Print span in mm as last printed token. Example around twelve mm.
