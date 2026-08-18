I run the post cycling teardown lab for pouch cells. After a bunch of fast charge cycles the polyethylene separator is full of metallic lithium that grew as thin needles. Those needles pierce the separator and lock away inventory that should have cycled. My imaging setup uses fluorescence of trapped lithium. The physics of scintillator diffusion and the camera point spread means every needle is smeared into a big fuzzy cloud. What you see is not the metal, it is the cloud.

I need you to write me a tiny standalone tool that tells me how much charge is actually locked in the main branching needles, so we can rank cells for field safety. The number I want is total trapped charge in milliCoulombs.

Please make a file at /app/solve.py. We call it like python /app/solve.py path to scan and we read the final printed token as the answer.

There is a single example volume you can try at /app/data/scene.ldch inside the container. That is just for you to debug. The hidden evaluation uses completely different volumes I made with new sizes spacings needle thickness brightness diffusion and pitch, passed as random temp file names. So you cannot hardcode numbers from the example. If you hardcode the example charge you will fail the hidden files.

File layout ldch. I made my own tiny container for this job. Everything is little endian.

Start four bytes ascii LDCH.
Next four bytes uint32 version.
Next four bytes uint32 dtype code. 2 means int16 voxels 16 means float32 voxels.
Next twelve bytes are three uint32 nx ny nz counts per axis.
Next twelve bytes are three float32 sx sy sz millimeters per voxel per axis. This changes every file so you must read it.
Next four bytes uint32 data offset where the voxel array begins.
At data offset you get nx times ny times nz samples in the dtype announced. X is fastest so linear index for x y z is x plus nx times y plus ny times z.

Inside each cube there is lithium metal in a few places. The real hazard is the long branching needles that cross the separator. Those are the only metal that counts for the charge I want. There are also round plating islands that sit flat on the anode surface. They are almost spherical and they are benign, you must not count them. They look round versus the needles look stretched. Rule of thumb we use in lab is a needle has longest bounding side at least eight voxels and more than one point six times its shortest side. Plating islands are cubic. In some scans there are also one to three very small bright specks far away that are dust on the window, ignore them.

Connectivity is twenty six neighbours in three dimensions.

Lab calibration: after we dissolve a known needle volume we measured that each cubic millimeter of solid lithium holds two point eight milliCoulombs of cyclable charge. So to get charge you first recover true metal volume in cubic millimeters from the smeared fluorescence, then multiply by two point eight.

Why simple brightness cut does not work. I tried. If I take a permissive dark level I pick up the whole skirt around every needle and my volume balloons to almost double. If I take a strict bright level I lose the thin tips that never get time to become fully bright and I lose a third to a half of the metal. Because each file has different background brightness, gain, and diffusion width, no single level works for all files. The needle interior is flat and bright but blur hides it.

The good news is blur does not create or destroy total fluorescence, it just moves it around. So total background-subtracted signal over needle plus its faint skirt divided by true core intensity gives number of true voxels, even when blurred. You will need a robust background estimate, a way to isolate the main branching needles from far dust and round islands, and a robust estimate of the core intensity that is not fooled by noise.

If you get those steps right you land within a percent. If you shortcut you are tens of percent off. Grading expects within three percent.

Coding rules. You must parse the bytes yourself, stdlib only. You can use struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any similar array imaging or graph library. Banned calls are eval exec compile __import__ chr. Banned tricks are subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing or trying to hide forbidden file names using chr bytes fromhex base64 b64decode bytearray tricks or string games. Do not try to open or list the tests folder. Do not mention or look for test_outputs heldout reference_charge _gen GEOM_TRUTH geometric_truth in your solver code. Your solver has to work on any random temp path they give, not a fixed path.

Print the charge in mC as the last thing you print.
