I work on the power module line in Penang. We mount SiC MOSFETs on DBC copper using silver sinter paste, Henkel ABLESTIK. After we press and sinter, solvent that did not fully burn out leaves sealed bubbles trapped between the die and the substrate. Those bubbles raise thermal resistance from junction to case and parts overheat in power cycling.

We inspect the sinter layer with a Phoenix nano focus X-ray at 160 kV. Silver and copper are dense and scatter a lot, the tube spot is not a point, and the scintillator spreads light. The result is a blur that keeps total X-ray counts but smears the bubble into a big fuzzy cloud. On the monitor a bubble that is really compact looks like a huge bright halo. We need the true bubble volume in cubic millimeters, not the cloudy size.

You have to write the tool.

Save it as /app/solve.py. We call python /app/solve.py with the scan file path and we use the last word you print as your answer.

We leave one attach layer scan at /app/data/scene.ssdv for you to try. You can open it while you code. Hidden grading uses completely different scans you have never seen, with different die sizes, voxel pitch, silver density, paste lot brightness, scatter width, background level, and noise. They are passed as random temporary files. Do not hardcode numbers from the example. If you hardcode the example volume you will fail.

File type is .ssdv, our own small format for silver sinter, all little endian.

First four bytes are letters SSDV.
Next four bytes are version uint32, currently one.
Next four bytes are dtype code uint32. Two means pixels are int16, sixteen means float32.
Next twelve bytes are three uint32 values nx ny nz, voxels along x y z.
Next twelve bytes are three float32 values sx sy sz, millimeters per voxel along x y z. They change per file and are anisotropic, so you must read them, we use different lenses so sx not equal sy not equal sz.
Next four bytes are uint32 offset where voxel data starts.
After that offset there are nx times ny times nz samples in the announced dtype, x moves fastest, so index equals x plus nx times y plus ny times z. We inverted during export so empty bubbles appear bright on silver.

What is inside. Each file has one main outgassing bubble that we grade. It is mostly round but has thin vent legs where gas tried to escape to the die edge. Those legs are shallow and never very bright but they belong to the bubble. Sometimes there are one or two tiny bright dots far away from the main bubble, left from organic residue or tiny unsintered paste clumps. Those dots must not be counted. Keep only the main bubble by 26 neighbour connectivity in 3D, pick the component with biggest total bright residual, not most voxels, because a shallow scratch can have many dim voxels but little energy.

Why counting voxels fails. If you count everything above a low level you include the big scatter halo and you get about double the real volume, sometimes more. If you count only very bright voxels you lose the thin vent legs and you get about half. No single level works for all lots because paste lot, die thickness, gain, blur width, and noise shift. Counting bright voxels is a proxy. Adding up total bright energy is the invariant.

Blur keeps energy. Scatter spreads counts but does not create or destroy counts. That lets us recover true volume though the bubble looks big. You need a pipeline. First find background silver level without letting the bubble bias you, use lower half of voxels. Then find noise sigma from median absolute deviation scaled by 1.4826. Then find main bubble and drop far specks using 26 connectivity biggest mass. Then find true interior height, not raw max with noise, but filtered 3 by 3 by 3 mean of top few voxels. Then grow outward layer by layer to include faint halo that belongs to bubble, stop when average of new shell falls to about noise floor, and make sure you do not bridge to a far speck. If you skip halo you undercount because much energy lives in halo when scatter is wide. If you include specks you overcount.

We grade within three percent relative error. Simple thresholds are far outside.

Implementation rules. Parse bytes yourself with struct only. Allowed imports are struct sys math random tempfile re. Banned are numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath and any array imaging graph helper. Banned builtins are eval exec compile import with double underscores chr. Do not use subprocess or os dot system popen exec fork walk listdir scandir open or pty importlib runpy ctypes or any directory listing. Do not hide paths with chr or bytes dot fromhex or base64 b64decode bytearray tricks. Never open or list the tests directory and never mention test_outputs heldout reference_volume underscore gen GEOM_TRUTH geometric_truth inside solve.py. Your code must work on random temporary files, not hardcoded.

Finally print volume in cubic millimeters as last token. Example final line 0.0159 as volume.
