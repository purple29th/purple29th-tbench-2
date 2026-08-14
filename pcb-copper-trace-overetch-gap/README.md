# PCB Copper Trace Overetch Gap - Wedge Clearance

## Summary
PCB etch line after resist develop, alkaline etchant attacks sidewall leaving triangular foot clearance called overetch wedge. MicroCT point spread smears clearance, plus detector pedestal and noise. Simple voxel counting fails across recipes.

This task requires from scratch Python script that parses custom binary .ovg with magic OVEG and reports true clearance volume in mm3 using attenuation conservation.

## Why This Is Hard
Point spread preserves total integrated attenuation despite smear, but threshold counting fails:
- Low isovalue keeps big glow and inflates 60-100pct
- High isovalue drops thin wedge foot and deflates 25-45pct
No single fixed cut works because gain and spread vary.

Correct method is pedestal-corrected sum divided by interior plateau level. Must separate main wedge from far dust grains, estimate pedestal without bias from wedge, estimate interior level robust to noise, and decide halo extent without merging flux bubbles.

To make it work you must:
* Parse header respecting payload offset, do not hardcode 64, read magic OVEG
* Keep only main wedge-shaped clearance via 26-connected clustering plus elongation vs compactness test, ignore round bubbles and far dust
* Estimate pedestal from lower half median plus MAD spread
* Estimate plateau from core top fraction
* Integrate halo with conservation and recover volume via sum/peak * pitch product

Method works for varied extents, pitches, gain, blur widths.

## Files
* /app/solve.py is file agent must create, prints volume as last word
* /app/data/scene.ovg and scene.pcb are samples for local dev with OVEG magic
* environment/Dockerfile installs python and pytest and copies both
* tests/test_outputs.py is evaluation suite with secure verifier

## Completion Criteria
Tests pass when volume error less than 3 percent tolerance on heldouts, similar to other precision void tasks. Requires wedge vs bubble shape discrimination; largest-by-mass vs largest-by-count.

## Model Analysis / Completion Rate
* Oracle 11/11 100 percent - reference solution passes all heldouts within 1 percent via attenuation conservation plus wedge filtering
* Naive threshold counting fails all heldouts by 60-100pct over or 25-45pct under
* Global conservation without bubble removal fails speck heavy case by more than 3pct because detached flux bubbles and dust grains contribute extra energy
* Shape discrimination required: wedge clearance triangular long along X vs spherical bubbles compact, aspect filter needed
* Expected difficulty: avocado 0/5 to 2/5, gpt 1/5, opus 2/5
* int16 dtype path exercised via heldout 2

## Anti Cheating
* No numpy, scipy, imaging libraries - from scratch only
* No hardcoded sample volume, must work on any random temp file path with OVEG magic
* Do not open or list /tests directory
* From scratch guard bans os, io, pathlib, tempfile etc via ALLOWED_MODULES
* Secure verifier generates heldouts at runtime in temp dir with jittered params and runs solver in isolated sandbox with audit hook blocking /tests, test_outputs, heldout, _gen plus inode hardlink guard via st_ino comparison and banned tempfile._os.link check
* Banned import check via AST in test_from_scratch
* Distance enforcement in jitter: specks far from main wedge by 25 and from each other by 15, to keep solvability

## Dedup Fix
Previously 0.79 Review vs sister pcb-copper-trace-undercut-gap (both PCBG, elongated vs round, same phrasing). Fixed to 0.27 Novel via distinct storyboard:
- Units: same mm3 but phrased as clearance vs gap volume, different jargon wedge vs undercut
- Physics story: alkaline sidewall attack triangular foot wedge clearance vs under-solder-mask undercut gap elongated along trace
- File format: OVEG vs PCBG magic, OVEG layout described with different field names (extents, pitches, payload start)
- Code style: helper names median_val, load_oveg, adjacent27, gap_volume vs median_sorted, read_pcb, trench_volume; variable names pedestal, spread, resid, active vs base, scatter, excess, hot; position helper pos() plus components logic, flood 25 iter guard
