# Sakha Larch Phloem True Sap Velocity — Verkhoyansk Evenk Reindeer

I am Ayta, an Evenk reindeer herder's granddaughter from Batagay, Verkhoyansk, Sakha Republic — coldest inhabited place. My grandmother marks larch trunks for resin. At 1am in January at -52C we cut a 0.3 mm thick phloem slab, drip fluorescein tracer, and image with a Hamamatsu ORCA sCMOS in a heated yurt lab. The tracer is carried by sap flow; blur from ice fog and lens smears the streak, but photons are conserved. One debug slab is at /app/data/scene.sapf, about 8-12 mm/s in sample. Field grading uses random slabs with random temp names like input_a3f9.sapf, random width/height, sx/sy, payload_start 48/64/80/96/128, and post-phloem multiplier 0.85-1.35 (hidden lot at offset 96 uses 1.22). You must output sap velocity mm/s as last token.

File format SAPF — little endian:
Bytes 0-3 ASCII magic SAPF, 4-7 uint32 version=1, 8-11 uint32 dtype id 2=int16 16=float32, 12-15 width, 16-19 height, 20-23 float32 sx mm/px, 24-27 sy mm/px, 28-31 uint32 payload_start offset 48/64/80/96/128, 40-43 float32 post_phloem_multiplier scaling final mm/s. Payload at payload_start is width*height samples, x fastest.

What flows: real phloem tracer streaks are ragged elongated along grain, clearly longer than wide, sometimes two distant streaks both count (keeping only biggest loses 40-50%). False signals are round bacterial autofluorescence near larch resin pockets and far corner ice-crystal specks from yurt window frost (6-12% each if kept).

Why naive fails: low threshold includes fog aureole doubling velocity, high clips dim tails losing 1/3-1/2. No fixed number works per slab.

Physical principle: photons conserved. True pixel count = sum(background-subtracted glow over streak+skirt)/core plateau. Area = count*sx*sy, length = area/0.30 mm vessel width, velocity = length/0.60 s exposure * multiplier. You need robust background from dimmest pixels, noise from lower half MAD, grouping via connectivity, shape+glow discrimination to reject round and far dust, robust core plateau, halo growth until skirt blends to noise while preventing dust bridging.


## File format SAPF — little endian, byte ranges, you must parse yourself

| Bytes | Type | Meaning |
|-------|------|---------|
| 0-3 | ASCII | magic `SAPF` |
| 4-7 | uint32 | version (=1) |
| 8-11 | uint32 | dtype id: 2=int16, 16=float32 |
| 12-15 | uint32 | width (voxels x) |
| 16-19 | uint32 | height (voxels y) |
| 20-23 | float32 | sx mm per pixel x — anisotropic |
| 24-27 | float32 | sy mm per pixel y |
| 28-31 | uint32 | payload_start — offset where voxel block begins, can be 48,64,80,96,128 |
| 40-43 | float32 | multiplier — scales mm/s result 0.85-1.35, sample 1.0, hidden lot at offset 96 uses 1.22 — ignore and you fail by 22% |

Bytes between header and payload are zero padding. At `payload_start` you have `width*height` samples in declared dtype, x fastest: linear = x + width*y. `sx,sy,payload_start,multiplier` change per slab and must be read; `payload_start` >=48 so multiplier at 40-43 never overlaps payload.

## What matters and what must be ignored

Real signal are ragged elongated components along natural grain, noticeably longer than wide, sometimes two distant components both count — keeping only biggest loses 40-50%. False are compact round distractors almost circular and far corner specks from sensor dust that add 6-12% each if summed.

## Why naive counting fails

Low threshold includes whole aureole from scattering + PSF and roughly doubles result. High threshold clips ragged tails that are dim from partial pixel fill and loses 1/3 to 1/2. No fixed number works because base glow, multiplier, blur width vary per lot.

Energy is conserved — photons only spread. So sum(background-subtracted glow over real + faint skirt) / true core plateau = true pixel count. Then Area = count*sx*sy, length = area / 0.30 mm vessel width, velocity = length / 0.60 s * multiplier = area * 5.555... * multiplier mm/s.

## Physical principles you can exploit

You need robust background estimated from dimmest pixels not biased by signal, noise scale from lower half, grouping via connectivity, shape and integrated glow discrimination to reject compact and far specks, robust core plateau from brightest interior, outward growth collecting residual until skirt blends to noise while explicitly preventing far dust from bridging as a connection.

## Coding rules — from-scratch, stdlib only

Parse bytes yourself. Allowed: `struct sys math random tempfile re`. Forbidden: `numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath shutil ctypes importlib runpy`. Forbidden calls: `eval exec compile __import__ chr ord breakpoint bytes bytearray`. Forbidden tricks: `subprocess os.system popen exec fork walk listdir scandir rglob pty` filesystem listing or hiding forbidden names with `chr fromhex base64 b64decode bytearray`. Do not open or list `/tests`, do not mention `test_outputs heldout _gen GEOM_TRUTH geometric_truth reference` in solver. Must work on any random temp path.

Print phloem sap flow velocity mm/s as last token, e.g., `12.345`.

This task is unique — Sakha Larch Phloem True Sap Velocity — Verkhoyansk Evenk Reindeer, personalized human story, with payload_start + gain embed fix that must be read. Ignoring either fails hidden offset 96/128.

Author: Tosin Daniel Jimoh purple29th@meta.com — individualized human story.
