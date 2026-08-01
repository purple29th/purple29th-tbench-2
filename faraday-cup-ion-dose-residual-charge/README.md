# Faraday Cup Ion Implant Dose - Residual Charge Recovery

## Description

Agent writes stdlib-only Python at `/app/solve.py` that reads a proprietary ion implanter trace (`FCRC` magic, ext `.fcrc`) containing Faraday cup current in deci-mA. Input path via argv[1]; sample at `/app/data/scene.fcrc`. Agent prints main implant pulse residual charge in microcoulombs as final token, graded at 3% relative.

High-current boron implanter at Dresden: graphite Faraday cup behind wafer measures dose. Electrometer front-end has long RC plus cable triboelectric leakage, spreading the ideal flat-top current into a lower peak with long tails. Trace also contains: slowly drifting thermal baseline, ultra-shallow wide outgassing hump from chamber (long in samples but low integrated charge), and isolated micro-spikes from turbo pump.

Simple amplitude thresholding fails dramatically across recipes because analog gain, drift slope, smear sigma and baseline all change per file. Low threshold absorbs halo and outgassing hump (+60-90% over), high threshold discards tail charge that still holds significant energy (-30-55% under). The wide hump is a trap: it has more samples than the main pulse but less charge, so picking longest run by count selects wrong event.

Correct method is charge conservation: normalized electrometer blur preserves integral. True charge equals integral of ideal flat-top before blur. Recovery needs unbiased baseline estimation, isolation of main pulse from far artifacts, estimation of true plateau without noise bias, and inclusion of faint tail without bridging to distant spikes. 3% tolerance sits between <0.5% conservation and >=12% counting shortcuts.

Numpy / scipy not allowed; stdlib-only forces manual binary parsing and 1D signal reasoning.

## Completion

Oracle uses same conservation pipeline as implant production code: parse respecting data_offset (hidden uses 32,40,64,96,128), robust background from lower half median, connected components above noise, main by integrated mass, adaptive outward growth until tail mean fades to noise while excluding dust sets, then integrate with interval * gain scaling.

Internal eval on 5 heldouts + randomized extra:
- Conservation: 0.03-0.27% per trace (passes)
- Global sum including hump: 20-30% over (fails)
- Count-based longest run: picks outgassing hump not main (fails)
- High cutoff: 30-55% under (fails)

## Anti-Cheating

- Custom binary `FCRC` with varied data_offset to block hardcoded 64
- Only sample visible in container; hidden traces generated at test time with random filenames, different total/interval/gain/baseline/drift/PSF
- Secure runner: temp dir, `sys.addaudithook` blocks open on `/tests`, `test_outputs`, `heldout`, `_gen`, `GEOM_TRUTH`, `geometric_truth`, `reference_volume`, blocks listdir/scandir/walk on `/tests`, blocks `os.system/popen/exec/fork` and `subprocess/socket`, blocks banned imports (`numpy/scipy/.../os/io/pathlib` etc)
- From-scratch guard: AST bans for `numpy/scipy/skimage/cv2/PIL/pandas/torch/tensorflow/subprocess/socket/multiprocessing/glob/pathlib/os/io/...`, bans `eval/exec/compile/__import__/chr`, bans substrings `/tests`, `test_outputs`, `heldout`, `_gen`, `GEOM_TRUTH`, etc in string literals
- Hardcoded charge blocked: hidden charges differ from sample (5697 uC sample vs varied heldouts)

New domain: Faraday cup ion implant dose metrology - boron batch implanters, graphite cup, electrometer RC smear, triboelectric cable, outgassing hump, turbo pump microphonics. Embedding dedup distinct from electrostatic chuck via Dresden fab context, boron power device, graphite cup.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
