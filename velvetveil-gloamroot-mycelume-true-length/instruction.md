# Velvetveil Gloamroot Mycelume True Length — Willamette Forest Foxfire

I am a field mycologist stationed at the H.J. Andrews Experimental Forest in Oregon. For three years I've been mapping *Armillaria ostoyae* — honey fungus — that makes the forest floor glow faintly after midnight, called foxfire. The fungus spreads via rhizomorphs: black shoestring cords that run under duff, 0.4 mm thick, branching along fallen Douglas fir grain. When they are metabolically active they emit a dim green photon veil from luciferase. My co-op of mushroom foragers wants to know total active cord length per duff slab to predict where the next bloom will be, because deer and boar dig there.

I image slabs at 1am with a Hamamatsu ORCA low-light sCMOS on a motorized stage. No flash, just 30-second exposures. The rig writes a tiny custom container we invented called MYCR (Mycelial Cord Radiance). One debug slab is at `/app/data/scene.mycr`, about 13-15 mm total glow length in our sample. Real field grading uses completely random slabs generated at runtime with random temp names like `input_a3f9.mycr`, random width/height, pixel pitch, background glow, blur, seed, and a post-veil calibration multiplier that varies per lot.

You must automate my grading. Write `/app/solve.py`. We run `python /app/solve.py /tmp/input_*.mycr` and take the last whitespace token as total illuminated cord length in mm.

## File format MYCR — little endian, byte ranges, you must parse yourself

| Bytes | Type | Meaning |
|-------|------|---------|
| 0-3 | ASCII | magic `MYCR` |
| 4-7 | uint32 | version (=1) |
| 8-11 | uint32 | dtype id: 2=int16, 16=float32 |
| 12-15 | uint32 | width (voxels x) |
| 16-19 | uint32 | height (voxels y) |
| 20-23 | float32 | sx mm per pixel x — anisotropic, file dependent |
| 24-27 | float32 | sy mm per pixel y |
| 28-31 | uint32 | payload_start — offset where voxel block begins, can be 48,64,80,96,128 |
| 40-43 | float32 | post_veil_multiplier — scales mm result 0.85-1.35, sample 1.0, hidden lot at offset 96 uses 1.22 — ignore and you fail by 22% |

Bytes between header and payload are zero padding. At `payload_start` you have `width*height` samples in declared dtype, x fastest: linear = x + width*y. `sx,sy,payload_start,post_veil_multiplier` change per slab and must be read; `payload_start` >=48 so multiplier at 40-43 never overlaps payload.

## What glows and what must be ignored

Inside each slab:

* **Real foxfire rhizomorphs**: ragged, elongated cords stretched along grain, 10-35 px long, length/width ratio >1.6. They are the signal. Some slabs have two distant cords (e.g., one near 15,20 and another near 60,45) both count — you must sum their recovered areas before converting to length, keeping only biggest loses 40-50% in double-cord slabs.
* **Round bacterial colonies** *Bacillus subtilis*: compact, almost circular photon blobs 3-5 px radius, ratio ~1, must be skipped. I call them false foxlights.
* **Far soil dust specks**: tiny bright dots in corners near (5,5) and (75,75) far from center, from camera window dust, 6-12% energy each if summed — must be skipped.

We use 8-neighbour connectivity in 2D to group glow.

## Why naive bright counting fails in my forest

Low threshold includes whole aureole from fog scattering + lens PSF and roughly doubles length. High threshold clips ragged hyphal tails that are dim from partial pixel fill and loses 1/3 to 1/2. No fixed number works because each slab has different duff base glow, multiplier, blur width.

Energy is conserved — photons only spread. So sum(base-subtracted glow over cord + faint skirt) / true core plateau = true pixel count. Then area = count * sx*sy, length = area / (0.4 mm repeat) * multiplier. I first undo blur to get true area, then length.

Lab pipeline that works:

1. Estimate robust duff base as median of dimmest 70% histogram so glow doesn't bias
2. Noise sigma as 1.4826*MAD of lower half around median
3. Mark candidates >4 sigma above base, 8-connected flood
4. Keep elongated groups (long side 10-35, ratio>1.6) and integrated glow >=0.35*biggest — that's ragged rhizomorph, drops round bacterial balls and far dust
5. Core plateau as mean of 4 brightest pixels inside kept cords (3x3 smoothed fallback if noisy)
6. Grow rings outward collecting residual until ring mean <=1*sigma, skipping dust groups to prevent bridging — that's halo recovery. Missing halo underestimates 15-25% because wide fog puts much energy in skirt.
7. Area = sum residual over expanded region / plateau * sx*sy, length = area * (1/0.4) * multiplier

Grade tolerance 3% relative. Simple thresholds are 50-130% off.

## Coding rules — from-scratch, stdlib only

Parse bytes yourself. Allowed: `struct sys math random tempfile re`. Forbidden: `numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath shutil ctypes importlib runpy`. Forbidden calls: `eval exec compile __import__ chr ord breakpoint bytes bytearray`. Forbidden tricks: `subprocess os.system popen exec fork walk listdir scandir rglob pty` filesystem listing or hiding forbidden names with `chr fromhex base64 b64decode bytearray`. Do not open or list `/tests`, do not mention `test_outputs heldout _gen GEOM_TRUTH geometric_truth reference_mass reference_length ground_truth` in solver. Must work on any random temp path.

Print length mm as last token, e.g., `13.462`.

This task is unique — Willamette foxfire rhizomorph photon veil, not an element, not mg, with payload_start + gain embed fix that must be read. Ignoring either fails hidden offset 96/128.

Author: Tosin Daniel Jimoh purple29th@meta.com — Willamette forest human story, individualized.

