# Atacama Salar Brine True Lithium Mass — Lickanantay Salt Harvester

I am Elena, a Lickanantay atacameña from Toconao, working the Salar de Atacama lithium brine pools at 2300m. At 1am we sample brine crust on glass slides, fluorescein-tagged lithium carbonate glows under 488nm. My family has harvested salt for generations, now lithium for batteries. The rig writes BRIN container, magic BRIN, with payload_start 48/64/80/96/128 and brine_multiplier at 40-43 (0.85-1.35, hidden 1.22 at 96). One debug slab is at /app/data/scene.brin, about 12-18 mg in sample. You must output true lithium mass mg as last token. Random temp names input_*.brin with varying dims, spacing, gain, blur.

File format BRIN: 0-3 SAP? actually BRIN magic, 4-7 version=1, 8-11 dtype 2=int16 16=float32, 12-15 width, 16-19 height, 20-23 sx mm/px, 24-27 sy, 28-31 payload_start, 40-43 post_brine_multiplier. Payload at payload_start width*height samples.

What crystallizes: real brine crystals are ragged elongated needles along salt grain, longer than wide, sometimes two distant pools both count. False are round halite dust compact circles and far corner salar dust specks from wind.

Why naive fails: low threshold includes salt aureole fog doubling mass, high clips dim needle tails losing 1/3-1/2.

Physical principle: photons conserved. Count = sum(residual)/plateau, area = count*sx*sy, thickness assumed 0.15 mm, density 2.11 mg/mm3, mass = area*thickness*density*multiplier = area*0.3165*multiplier mg. Need robust background median dimmest %, MAD noise, connectivity, shape+glow filter, core plateau from brightest interior, halo growth to noise floor skipping far dust.


## File format BRIN — little endian, byte ranges, you must parse yourself

| Bytes | Type | Meaning |
|-------|------|---------|
| 0-3 | ASCII | magic `BRIN` |
| 4-7 | uint32 | version (=1) |
| 8-11 | uint32 | dtype id: 2=int16, 16=float32 |
| 12-15 | uint32 | width (voxels x) |
| 16-19 | uint32 | height (voxels y) |
| 20-23 | float32 | sx mm per pixel x — anisotropic |
| 24-27 | float32 | sy mm per pixel y |
| 28-31 | uint32 | payload_start — offset where voxel block begins, can be 48,64,80,96,128 |
| 40-43 | float32 | multiplier — scales mg result 0.85-1.35, sample 1.0, hidden lot at offset 96 uses 1.22 — ignore and you fail by 22% |

Bytes between header and payload are zero padding. At `payload_start` you have `width*height` samples in declared dtype, x fastest: linear = x + width*y. `sx,sy,payload_start,multiplier` change per slab and must be read; `payload_start` >=48 so multiplier at 40-43 never overlaps payload.

## What matters and what must be ignored

Real signal are ragged elongated components along natural grain, noticeably longer than wide, sometimes two distant components both count — keeping only biggest loses 40-50%. False are compact round distractors almost circular and far corner specks from sensor dust that add 6-12% each if summed.

## Why naive counting fails

Low threshold includes whole aureole from scattering + PSF and roughly doubles result. High threshold clips ragged tails that are dim from partial pixel fill and loses 1/3 to 1/2. No fixed number works because base glow, multiplier, blur width vary per lot.

Energy is conserved — photons only spread. So sum(background-subtracted glow over real + faint skirt) / true core plateau = true pixel count. Then mass = area * 0.15 mm * 2.11 mg/mm3 * multiplier = area*0.3165*multiplier mg.

## Physical principles you can exploit

You need robust background estimated from dimmest pixels not biased by signal, noise scale from lower half, grouping via connectivity, shape and integrated glow discrimination to reject compact and far specks, robust core plateau from brightest interior, outward growth collecting residual until skirt blends to noise while explicitly preventing far dust from bridging as a connection.

## Coding rules — from-scratch, stdlib only

Parse bytes yourself. Allowed: `struct sys math random tempfile re`. Forbidden: `numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath shutil ctypes importlib runpy`. Forbidden calls: `eval exec compile __import__ chr ord breakpoint bytes bytearray`. Forbidden tricks: `subprocess os.system popen exec fork walk listdir scandir rglob pty` filesystem listing or hiding forbidden names with `chr fromhex base64 b64decode bytearray`. Do not open or list `/tests`, do not mention `test_outputs heldout _gen GEOM_TRUTH geometric_truth reference` in solver. Must work on any random temp path.

Print lithium brine mass mg as last token, e.g., `12.345`.

This task is unique — Atacama Salar Brine True Lithium Mass — Lickanantay Salt Harvester, personalized human story, with payload_start + gain embed fix that must be read. Ignoring either fails hidden offset 96/128.

Author: Tosin Daniel Jimoh purple29th@meta.com — individualized human story.
