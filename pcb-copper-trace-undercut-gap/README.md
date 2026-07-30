# PCB Copper Trace Undercut Gap

## Summary
I work on PCB factory line. After etching, copper traces have undercut that creates a small gap under solder mask. This gap hurts reliability. We use X ray to see it but X ray blur spreads the gap signal everywhere, so the gap looks larger and fuzzier than its true size.

This task requires a from scratch Python script that parses custom binary .pcb and reports true gap volume in mm3.

## Why This Is Hard
X ray blur makes threshold counting imprecise. Low cutoff includes huge halo and overcounts by 80 to 130 percent. High cutoff misses thin undercut that never gets bright enough and undercounts by 30 to 50 percent. No fixed cutoff works across files because brightness and blur width change.

Correct method is intensity conservation. Total X ray signal is conserved despite blur. So true gap voxels equals sum of background subtracted intensity divided by plateau intensity.

To make it work you must separate main gap from far specks using 26 neighbour connectivity, estimate background without bias from gap itself, estimate true plateau intensity without being fooled by noise, and decide how far faint halo extends without merging specks. That is the hard part.

## Approach
Similar to other precision void tasks, you need to:
* Parse header respecting data offset, do not hardcode 64
* Keep only main connected bright mass, ignore far dust specks
* Estimate background from border voxels far from gap
* Estimate plateau from core flat region
* Integrate halo with conservation and recover volume

Method works for varied dimensions, spacings, brightness, blur widths.

## Files
* /app/solve.py is file agent must create, prints volume as last word
* /app/data/scene.pcb is sample for local dev
* environment/Dockerfile installs python and pytest
* tests/test_outputs.py is evaluation suite

## Completion Criteria
Tests pass when volume error less than 3 percent tolerance on heldouts, similar to other precision tasks.

## Anti Cheating
* No numpy, scipy, imaging libraries - from scratch only
* No hardcoded sample volume, must work on any random temp file path
* Do not open or list /tests directory
* From scratch guard bans os, io, pathlib etc
