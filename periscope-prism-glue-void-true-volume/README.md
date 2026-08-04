# Periscope Prism Glue Void True Volume

I inspect periscope telephoto modules that fold light with a large glass prism bonded to plastic barrel with UV glue. Trapped air after cure forms sealed pockets in adhesive that shift under OIS and cause moving flare in image QA. I screen modules with 160kV micro focus cone beam CT.

Physics: finite focal spot plus scintillator bleed plus scatter inside thick glass acts as normalized anisotropic low pass. Total integrated excess over background stays constant, but energy spreads into wide halo, so bubble looks much larger than reality.

Input is custom binary .apcv magic APCV with anisotropic pitch sx sy sz mm, dimensions nx ny nz, dtype int16 id 2 or float32 id 16, x fastest, contrast inverted so voids bright. Task asks volume in cubic mm as last token. Only principal sealed pocket counts, far dust specks on prism facet must be ignored, but they must be sub millimeter and one to two per volume, not large. Simple bright count overestimates near double by halo or underestimates half by missing thin glue tails along chamfer, and no universal cutoff works because tube brightness, glass absorption, smear width and noise drift per lot.

Intended solver uses conservation true voxels equals sum background subtracted over void plus halo divided by plateau. To hit three percent you need careful background from median, noise from lower half MAD, dust exclusion via largest integrated residual under twenty six connectivity, plateau from most concentrated region via three by three by three mean filtered top four, inclusive halo growth until shell mean drops to noise without bridging to distant specks.

This task is hardware CT inspection, not Android Kotlin software. It belongs to data science track with python slim base and pytest grading. Tag android was removed to avoid Android Guidebook non Android filler pattern. Previous version was flagged as 12 line diff from diecast aluminum pore, this version rewrites solver with distinct function names and linear drift handling and explicit 96 and 128 data offset cases.

Validation: secure verifier generates heldouts at runtime with random temp filenames, varied grid pitch amplitude background PSF noise, data offset varied 32 40 48 64 80 96 128. Sample at /app/data/scene.apcv around 560 mm3, heldouts larger. Oracle stdlib only conservation with median lower half baseline, MAD noise, largest mass 26 connected isolation, 3x3x3 mean filter plateau top four, halo growth to noise floor, measured under one percent.

Negative controls:
* Low cutoff includes halo 80 to 130 over
* Fixed absolute 30 worst
* Half max Otsu 18 to 36 off
* Global sum without speck removal fails speck heavy by more than 8 percent over now that specks are sub mm at 5 to 9 percent mass each
* Missing halo 15 to 25 under

Tolerance three percent sits between one percent sound conservation and twelve percent counting shortcuts.

Anti cheating: No generator mounted, geometric truth recomputed inside verifier. solve.py executed in isolated TemporaryDirectory with neutral name, PYTHONPATH set, audit hook blocks open on /tests test_outputs heldout geometric_truth reference_volume, blocks listdir scandir walk, blocks system popen exec fork spawn and subprocess socket, blocks banned imports. test_from_scratch bans numpy scipy skimage cv2 PIL pandas torch tensorflow subprocess socket multiprocessing glob pathlib os io posixpath ntpath genericpath shutil and calls eval exec compile __import__ chr ord breakpoint bytes bytearray.

Hardcoded volume blocked: sample differs from hidden.

Author Tosin Daniel Jimoh purple29th at meta.com
