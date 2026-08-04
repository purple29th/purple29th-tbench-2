# Android Piezo Haptic Residual Charge

## What this task is
I work on haptics for Android flagships that use under display piezo stacks for crisp clicks. The piezo is driven high voltage, then we look at residual current that drains from the stack and the elastomer gasket. If we integrate the wrong part the click feels mushy and we get QA fails. This task asks a solver to write stdlib only Python at /app/solve.py that reads my proprietary trace APHC magic ext aphc and prints true residual charge of main pop in microcoulombs, graded at 3 percent relative. Sample at /app/data/scene.aphc.

This is not a simple copy of pvd magnetron or faraday cup or electrostatic chuck, even though they share charge conservation core. Those older tasks have single hump plus linear drift only. This piezo task has two distinct shallow wide humps from different physics, one from piezo dielectric absorption creep and one from elastomer gasket relaxation, plus sinusoidal RF ripple from display driver at 120 to 250 sample period, plus linear thermal drift that changes slope per file, plus gain trim that multiplies charge. The combination makes longest run by count pick the wrong hump, and dual humps together are longer than main pop plus 30 samples. You must pick main pop by integrated mass not by count, and you must not bridge to creep humps or LRA spikes.

## Why earlier runs were marked ambiguous
Earlier spec wording said samples convert to mA as value divided by 10, while tests multiply by gain. That was ambiguous. This version fixes it: raw deci mA value divided by 10 gives raw mA, calibrated mA equals raw mA times gain trim from header offset 20. Charge in microcoulombs equals sum of calibrated mA over main plus tails minus drifting baseline times interval seconds times 1000. Example: sample 250 means 25.0 raw mA, gain 1.2 gives 30.0 calibrated mA, interval 0.0008 seconds, sum 1000 samples gives 24 mC converted to 24000 uC, but main pop is only fraction. If you ignore gain you are low by gain factor 0.85 to 1.35 and you fail non unit gain hidden tests. This is now stated explicitly in instruction with example calculation.

## How this version is materially different from its siblings
To address novelty HIGH vs pvd magnetron arc residual charge and others:

* File layout is APHC with total as uint32 N int16 samples, data_offset varied includes 96 and 128 padding explicitly tested, plus interval float32 and gain trim float32 and baseline hint, plus RF fields rf_amp rf_period in test generation that bleed into baseline
* Solver implemented here uses linear drift estimation from edge medians with slope, not just flat median, plus RF ripple awareness, plus 3.2 sigma threshold not 3.5, plus 60 step dilation to 0.5 sigma while excluding dust sets built from other clusters
* Code structure is rewritten with distinct function names load_aphc, robust_median, estimate_drift_and_baseline, find_pop_clusters, grow_tail, compute_charge_uC, very different patch from pvd 2 line diff
* Tests extended with heldout_96 and heldout_128 for data_offset coverage, and from scratch guard now also bans ord breakpoint bytes bytearray shutil to align with spec forbidden list
* Instruction now includes gain formula and example, plus explicit note that sample file gain 1.0 hides effect but hidden uses non unit gain

## Completion criteria
Oracle parse respecting data_offset 32 40 48 64 80 96 128, robust baseline from lower half median plus low value median and linear drift from edges, mass based main pop, tail dilation until 0.5 sigma, charge via total_res divided by 10 times interval times gain times 1000.

Internal eval 7 heldouts now plus extra:
* Conservation 0.1 to 0.6 percent passes
* Global sum including both dual creep humps 25 to 45 percent over fails
* Count based longest run picks hump fails 60 percent+
* Dual hump count trap ww1 plus ww2 greater than main plus 30 validated
* Gain sensitivity: no gain version low by gain factor fails 0.85 to 1.35 cases
* data_offset 96 and 128 exercised

Harder than single hump Faraday family due to dual humps plus RF sine baseline plus gain calibration.

## Anti cheating
* Custom APHC binary, varied data_offset blocks hardcode 64
* Only sample visible, hidden traces generated at runtime with random filenames varied total interval gain baseline drift PSF RF
* Secure runner with sys.addaudithook blocks open on /tests test_outputs heldout _gen GEOM_TRUTH geometric_truth reference_volume, blocks listdir scandir walk, blocks os.system popen exec fork and subprocess socket, blocks banned imports
* From scratch guard bans numpy scipy etc and os io pathlib shutil and eval exec compile __import__ chr ord breakpoint bytes bytearray
* Hardcoded charge blocked

Author Tosin Daniel Jimoh purple29th at meta.com
