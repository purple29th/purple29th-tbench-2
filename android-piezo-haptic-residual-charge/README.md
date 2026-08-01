# Android Piezo Haptic Residual Charge

## Description

Agent writes stdlib-only Python at `/app/solve.py` that reads a proprietary piezo haptic trace (`APHC` magic, ext `.aphc`) from Android flagship under-display piezo actuator. Sample at `/app/data/scene.aphc`. Agent prints main haptic pop residual charge in microcoulombs, graded at 3% relative.

Under-display piezo stack for crisp clicks: dielectric absorption plus elastomer gasket relaxation causes slow creep. Driver RC spreads ideal flat-top into broad peak with tails. Trace also contains linear thermal drift plus sinusoidal RF ripple from display driver, dual wide shallow humps (dielectric creep + elastomer relaxation) each long but low charge, and far spikes from LRA cross-talk and finger tap.

Thresholding fails across devices because gain, drift slope, RF amplitude/period, smear width vary. Low threshold absorbs halo + both humps + RF crests (+65-95% over), high threshold cuts tail charge (-30-50% under). Longest run by count picks creep hump not main pop; dual humps together even longer in count but less charge.

Correct method conserves charge: normalized blur preserves integral. Recovery needs unbiased baseline despite RF sine, isolation of main pop from dual humps and far spikes, plateau estimation, tail inclusion until noise floor while not bridging to distant artifacts.

## Completion

Oracle: parse respecting data_offset (hidden 32/40/48/64/80/96/128), robust background from lower half median + low-value median refinement, components above noise, main by integrated mass not count, adaptive dilation until shell mean fades to 0.5 sigma while excluding dust sets, integrate with interval*gain.

Internal eval 5 heldouts + extra:
- Conservation 0.1-0.6% passes
- Global sum including both humps 25-45% over fails
- Count-based longest run picks hump fails 60%+
- Dual hump count trap ww1+ww2 > main+30 validated

Harder than single-hump Faraday family due to dual creep humps + RF sinusoidal baseline.

## Anti-Cheating

- Custom `APHC` binary, varied data_offset blocks hardcode 64
- Only sample visible; hidden traces generated at test time with random filenames, varied total/interval/gain/baseline/drift/PSF/RF
- Secure runner temp dir, `sys.addaudithook` blocks open on `/tests`, `test_outputs`, `heldout`, `_gen`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, blocks listdir/scandir/walk, blocks `os.system/popen/exec/fork` and `subprocess/socket`, blocks banned imports
- From-scratch guard bans `numpy/scipy/.../os/io/pathlib` etc, bans `eval/exec/compile/__import__/chr`
- Hardcoded charge blocked: hidden charges differ from sample

New domain: Android under-display piezo haptics - crisp click, dielectric absorption, elastomer gasket creep, LRA cross-talk, RF ripple from display driver. Distinct from Faraday cup dose and electrostatic chuck and PVD magnetron despite same conservation core.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
