I work on EUV pellicle inspection in the fab. The pellicle is a freestanding membrane that protects the reticle. During EUV exposure hydrocarbons crack and grow carbon soot on the membrane. That soot absorbs EUV and heats, so we need to know total carbon mass in micrograms on the membrane to decide when to replace it.

The problem is we image carbon with X-ray fluorescence where soot glows bright, but diffusion in the scintillator plus the lens point spread smears the glow everywhere. What you see is a big fuzzy cloud, not the true soot.

I need you to write me a tiny tool that tells me total carbon mass in micrograms for the main branching soot streaks.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read the final printed token as the answer.

There is a single example volume you can try at /app/data/scene.epcm inside the container. That is just for you to debug. The hidden evaluation uses completely different volumes I made with new sizes spacings soot thickness brightness diffusion and pitch passed as random temp file names. So you cannot hardcode numbers from the example. If you hardcode the example mass you will fail the hidden files.

File layout epcm. I made my own tiny container for this job. Everything is little endian.

Start four bytes ascii EPCM.
Next four bytes uint32 version.
Next four bytes uint32 dtype code. 2 means int16 voxels 16 means float32 voxels.
Next twelve bytes are three uint32 nx ny nz counts per axis.
Next twelve bytes are three float32 sx sy sz millimeters per voxel per axis. This changes every file so you must read it.
Next four bytes uint32 data offset where the voxel array begins.
At data offset you get nx times ny times nz samples in the dtype announced. X is fastest so linear index for x y z is x plus nx times y plus ny times z.

Inside each cube there is carbon soot in a few places. The real contamination is the long branching streaks that follow crazing on the membrane. Those are the only soot that counts for mass. There are also round airborne particles that sit on the surface. They are almost spherical and they are benign, you must not count them. They look round versus the streaks look stretched. Rule of thumb we use in lab is a streak has longest bounding side at least eight voxels and more than one point six times its shortest side. Airborne particles are cubic. In some scans there are also one to three very small bright specks far away that are dust on the window, ignore them.

Connectivity is twenty six neighbours in three dimensions.

Lab calibration: after we plasma ash a known streak volume we measured that each cubic millimeter of solid carbon soot holds two point one micrograms. So to get mass you first recover true soot volume in cubic millimeters from the smeared fluorescence, then multiply by two point one.

Why simple brightness cut does not work. I tried. If I take a permissive dark level I pick up the whole skirt around every streak and my volume balloons to almost double. If I take a strict bright level I lose the thin tips that never get time to become fully bright and I lose a third to a half of the soot. Because each file has different background brightness, gain, and diffusion width, no single level works for all files. The streak interior is flat and bright but blur hides it.

The good news is blur does not create or destroy total fluorescence, it just moves it around. So total background subtracted signal over streak plus its faint skirt divided by true core intensity gives number of true voxels, even when blurred. To use that you need to get an unbiased background estimate from border region, isolate the main branching streaks from far dust and round islands using mass and shape, get a robust core intensity from the most concentrated spot without being fooled by noise using three by three by three local smoothing plus top four mean, and then expand outward step by step until the shell average falls to about the noise floor, being careful not to jump into a dust ball.

If you get those steps right you land within a percent. If you shortcut you are tens of percent off. Grading expects within three percent.

Coding rules. You must parse the bytes yourself, stdlib only. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any similar array imaging or graph library. Banned calls are eval exec compile __import__ chr. Banned tricks are subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or trying to hide forbidden file names using chr bytes fromhex base64 b64decode bytearray tricks or string games. Do not try to open or list the tests folder. Do not mention or look for test_outputs heldout reference_charge _gen GEOM_TRUTH or geometric_truth in your solver code. Your solver has to work on any random temp path they give, not a fixed path.

Print the mass in ug as the last thing you print.
