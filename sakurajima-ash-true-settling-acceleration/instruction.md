# Sakurajima Ash True Settling Acceleration — Kagoshima Tea Farmer

I am Haru, a tea farmer from Sakurajima, Kagoshima, Japan. Sakurajima erupts daily, ash falls on tea leaves, stunts growth. At 1am we image ash fall streaks on sticky glass slides with IR phosphor, tracer shows settling dynamics. Blur from humid air and lens smears but conserves photons. Rig writes ASHF container, magic ASHF, payload_start 48/64/80/96/128, ash_multiplier at 40-43 (hidden 1.22). Debug at /app/data/scene.ashf about 6-10 mm/s^2. Output settling acceleration mm/s^2 as last token. Random temp names input_*.ashf.

File format ASHF: 0-3 magic ASHF, 4-7 version=1, 8-11 dtype, 12-15 width, 16-19 height, 20-23 sx, 24-27 sy, 28-31 payload_start, 40-43 multiplier.

What falls: real ash streaks are elongated ragged along wind grain, longer than wide, sometimes two distant streaks. False are round condensed water droplets compact and far corner ash specks.

Why naive fails: fog doubles acceleration, high clips tails.

Physical principle: photons conserved. Count = sum(residual)/plateau, area = count*sx*sy, length = area/0.35 mm grain, velocity = length/0.80 s exposure, acceleration = velocity/1.20 s * multiplier = area*2.976...*multiplier mm/s^2. Need robust background, MAD, connectivity, shape filter, plateau, halo growth.


## File format ASHF — little endian, byte ranges, you must parse yourself

| Bytes | Type | Meaning |
|-------|------|---------|
| 0-3 | ASCII | magic `ASHF` |
| 4-7 | uint32 | version (=1) |
| 8-11 | uint32 | dtype id: 2=int16, 16=float32 |
| 12-15 | uint32 | width (voxels x) |
| 16-19 | uint32 | height (voxels y) |
| 20-23 | float32 | sx mm per pixel x — anisotropic |
| 24-27 | float32 | sy mm per pixel y |
| 28-31 | uint32 | payload_start — offset where voxel block begins, can be 48,64,80,96,128 |
| 40-43 | float32 | multiplier — scales mm/s^2 result 0.85-1.35, sample 1.0, hidden lot at offset 96 uses 1.22 — ignore and you fail by 22% |

Bytes between header and payload are zero padding. At `payload_start` you have `width*height` samples in declared dtype, x fastest: linear = x + width*y. `sx,sy,payload_start,multiplier` change per slab and must be read; `payload_start` >=48 so multiplier at 40-43 never overlaps payload.

## What matters and what must be ignored

Real signal are ragged elongated components along natural grain, noticeably longer than wide, sometimes two distant components both count — keeping only biggest loses 40-50%. False are compact round distractors almost circular and far corner specks from sensor dust that add 6-12% each if summed.

## Why naive counting fails

Low threshold includes whole aureole from scattering + PSF and roughly doubles result. High threshold clips ragged tails that are dim from partial pixel fill and loses 1/3 to 1/2. No fixed number works because base glow, multiplier, blur width vary per lot.

Energy is conserved — photons only spread. So sum(background-subtracted glow over real + faint skirt) / true core plateau = true pixel count. Then length=area/0.35, velocity=length/0.80, acceleration=velocity/1.20*multiplier = area*2.976*multiplier mm/s^2.

## Physical principles you can exploit

You need robust background estimated from dimmest pixels not biased by signal, noise scale from lower half, grouping via connectivity, shape and integrated glow discrimination to reject compact and far specks, robust core plateau from brightest interior, outward growth collecting residual until skirt blends to noise while explicitly preventing far dust from bridging as a connection.

## Coding rules — from-scratch, stdlib only

Parse bytes yourself. Allowed: `struct sys math random tempfile re`. Forbidden: `numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath shutil ctypes importlib runpy`. Forbidden calls: `eval exec compile __import__ chr ord breakpoint bytes bytearray`. Forbidden tricks: `subprocess os.system popen exec fork walk listdir scandir rglob pty` filesystem listing or hiding forbidden names with `chr fromhex base64 b64decode bytearray`. Do not open or list `/tests`, do not mention `test_outputs heldout _gen GEOM_TRUTH geometric_truth reference` in solver. Must work on any random temp path.

Print ash settling acceleration mm/s^2 as last token, e.g., `12.345`.

This task is unique — Sakurajima Ash True Settling Acceleration — Kagoshima Tea Farmer, personalized human story, with payload_start + gain embed fix that must be read. Ignoring either fails hidden offset 96/128.

Author: Tosin Daniel Jimoh purple29th@meta.com — individualized human story.
