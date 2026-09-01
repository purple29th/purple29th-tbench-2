# Mekong Mangrove Burrow True Oxygen Flux — Ca Mau Fisher Daughter

I am Linh, a fisher's daughter from Ca Mau, Mekong Delta, Vietnam. My father farms mudskippers in mangrove burrows. At 1am we image burrow cross-sections with oxygen-sensitive phosphor that glows where O2 leaks. Phosphor blur from mud turbidity smears glow but conserves photons. The rig writes BURW container, magic BURW, payload_start 48/64/80/96/128, burrow_multiplier at 40-43 (hidden 1.22 at 96). Debug slab at /app/data/scene.burw about 15-22 uL/min. Output oxygen flux uL/min as last token. Random temp names input_*.burw.

File format BURW: 0-3 magic BURW, 4-7 version=1, 8-11 dtype, 12-15 width, 16-19 height, 20-23 sx, 24-27 sy, 28-31 payload_start, 40-43 multiplier. Payload at offset.

What breathes: real burrow channels are elongated ragged along root grain, longer than wide, sometimes two distant channels. False are round crab-pellet blobs and far corner mud specks.

Why naive fails: fog aura doubles flux, strict clips tails losing half.

Physical principle: photons conserved. Count = sum(residual)/plateau, area = count*sx*sy, flux = area * 0.45 uL/min/mm2 * multiplier. Need robust background, MAD, connectivity, shape filter, plateau, halo growth preventing dust bridge.


## File format BURW — little endian, byte ranges, you must parse yourself

| Bytes | Type | Meaning |
|-------|------|---------|
| 0-3 | ASCII | magic `BURW` |
| 4-7 | uint32 | version (=1) |
| 8-11 | uint32 | dtype id: 2=int16, 16=float32 |
| 12-15 | uint32 | width (voxels x) |
| 16-19 | uint32 | height (voxels y) |
| 20-23 | float32 | sx mm per pixel x — anisotropic |
| 24-27 | float32 | sy mm per pixel y |
| 28-31 | uint32 | payload_start — offset where voxel block begins, can be 48,64,80,96,128 |
| 40-43 | float32 | multiplier — scales uL/min result 0.85-1.35, sample 1.0, hidden lot at offset 96 uses 1.22 — ignore and you fail by 22% |

Bytes between header and payload are zero padding. At `payload_start` you have `width*height` samples in declared dtype, x fastest: linear = x + width*y. `sx,sy,payload_start,multiplier` change per slab and must be read; `payload_start` >=48 so multiplier at 40-43 never overlaps payload.

## What matters and what must be ignored

Real signal are ragged elongated components along natural grain, noticeably longer than wide, sometimes two distant components both count — keeping only biggest loses 40-50%. False are compact round distractors almost circular and far corner specks from sensor dust that add 6-12% each if summed.

## Why naive counting fails

Low threshold includes whole aureole from scattering + PSF and roughly doubles result. High threshold clips ragged tails that are dim from partial pixel fill and loses 1/3 to 1/2. No fixed number works because base glow, multiplier, blur width vary per lot.

Energy is conserved — photons only spread. So sum(background-subtracted glow over real + faint skirt) / true core plateau = true pixel count. Then flux = area * 0.45 uL/min/mm2 * multiplier.

## Physical principles you can exploit

You need robust background estimated from dimmest pixels not biased by signal, noise scale from lower half, grouping via connectivity, shape and integrated glow discrimination to reject compact and far specks, robust core plateau from brightest interior, outward growth collecting residual until skirt blends to noise while explicitly preventing far dust from bridging as a connection.

## Coding rules — from-scratch, stdlib only

Parse bytes yourself. Allowed: `struct sys math random tempfile re`. Forbidden: `numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath shutil ctypes importlib runpy`. Forbidden calls: `eval exec compile __import__ chr ord breakpoint bytes bytearray`. Forbidden tricks: `subprocess os.system popen exec fork walk listdir scandir rglob pty` filesystem listing or hiding forbidden names with `chr fromhex base64 b64decode bytearray`. Do not open or list `/tests`, do not mention `test_outputs heldout _gen GEOM_TRUTH geometric_truth reference` in solver. Must work on any random temp path.

Print burrow oxygen flux uL/min as last token, e.g., `12.345`.

This task is unique — Mekong Mangrove Burrow True Oxygen Flux — Ca Mau Fisher Daughter, personalized human story, with payload_start + gain embed fix that must be read. Ignoring either fails hidden offset 96/128.

Author: Tosin Daniel Jimoh purple29th@meta.com — individualized human story.
