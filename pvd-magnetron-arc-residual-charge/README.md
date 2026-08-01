# PVD Magnetron Arc Residual Charge

## Description

Agent writes stdlib-only Python at `/app/solve.py` that reads a proprietary PVD magnetron sputter trace (`PMAR` magic, ext `.pmar`) containing target arc current in deci-mA. Sample at `/app/data/scene.pmar`. Agent prints main arc residual charge in microcoulombs, graded at 3% relative.

PVD tool sputters ITO on display glass. Magnetron at high power arcs: bias cable sees a flat-top ideal current smeared by electrometer low-pass into broad peak with tails. Trace hardens: linear thermal drift plus sinusoidal RF pickup from magnetron PSU (wavy baseline), two shallow wide humps (target poisoning outgassing and anodic afterglow) each long but low charge, and far spikes from shutter vibration. Dual humps are the new trap: together they span more samples than main arc but less total charge.

Thresholding fails by large margin across chambers because gain, drift slope, RF amplitude/period, smear sigma all vary. Low threshold absorbs halo + both humps + RF crests (+70-100% over), high threshold cuts tail charge (-35-60% under). Longest run by sample count picks a wide hump, not main, and even sum of both humps count > main count but charge less.

Correct approach conserves charge: normalized blur preserves integral. Recovery needs unbiased baseline despite RF sine, isolation of main arc from dual humps and far spikes, estimation of true plateau, inclusion of faint tail until noise floor while not bridging to distant artifacts. 3% tolerance sits between <0.5% conservation and >=15% shortcuts.

## Completion

Oracle uses production-style pipeline: parse respecting data_offset (hidden uses 16,32,48,64,80,96,128), robust background from median of lower half plus low-value median refinement, connected components above noise, main by integrated mass (not count), adaptive dilation until shell mean fades to 0.5 sigma while excluding dust sets, integrate with interval*gain scaling.

Internal eval 5 heldouts + extra:
- Conservation 0.1-0.5% passes
- Global sum including both humps 25-40% over fails
- Count-based longest run picks hump fails
- Dual hump count trap: ww1+ww2 > main width validated

Harder than Faraday family due to dual humps + sinusoidal RF baseline.

## Anti-Cheating

- Custom `PMAR` binary, varied data_offset blocks hardcode 64
- Only sample visible; hidden traces generated at test time with random filenames, varied total/interval/gain/baseline/drift/PSF/RF amp/period
- Secure runner: temp dir, `sys.addaudithook` blocks open on `/tests`, `test_outputs`, `heldout`, `_gen`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, blocks listdir/scandir/walk, blocks `os.system/popen/exec/fork` and `subprocess/socket`, blocks banned imports
- From-scratch guard bans `numpy/scipy/.../os/io/pathlib` etc, bans `eval/exec/compile/__import__/chr`, bans substrings `/tests`, `test_outputs` etc
- Hardcoded charge blocked: hidden charges differ from sample

New domain: PVD magnetron sputter target arcing - ITO display glass, target poisoning, anodic afterglow, RF PSU sinusoidal interference, shutter vibration. Distinct from Faraday cup dose and electrostatic chuck despite same conservation core.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
