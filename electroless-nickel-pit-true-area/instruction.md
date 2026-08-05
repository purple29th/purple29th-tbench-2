We plate car connector pins with electroless nickel and a bubble defect makes us fail salt spray.

I am on the automotive pin line. We do Ni-P about twelve microns on copper. Sometimes hydrogen sticks during plating and you get a little pit down to copper. When that panel goes to salt spray it rusts red and the customer rejects.

We measure with a white light interferometer. The picture lies. Airy disk plus stage wobble plus fringe noise blur a tiny deep pit into a wide shallow dish. What is really round and deep looks like a big soft cloud on screen. We need true pit area mm2, not the cloud size.

Write a program.

Put it at /app/solve.py. We will call python /app/solve.py /path/to/file.enpp and we read the last token you print as the answer.

For local dev we left one example at /app/data/scene.enpp you can open. Hidden tests use totally different files you never saw, different sizes, pixel spacing, brightness, blur, tilt, noise. Do not hard code anything from the example file, if you do you will fail hidden.

File is custom binary ENPP, little endian. It starts with 4 byte magic ENPP, then version, dtype, dims, spacing, data offset, then pixel values. Dtype 2 is int16, 16 is float32. Dims are nx ny counts, spacing sx sy is mm per pixel for x and y, anisotropic, you must use it. Offset tells where pixels start. Pixels are nx times ny, x fastest so index is x plus nx times y. We flipped so pits look bright.

Inside. One main pit per file is what we score. It is roundish but there are two thin lips left and right where bubble was pinned, those lips count as part of pit even though they look dim after smear because fractional coverage. Sometimes there are one or two tiny bright dots far from main pit from dust, and sometimes a wide shallow scratch far away covering many pixels but dim. Ignore those, main pit is the dominant bright blob.

Fixed level does not work. Low level makes you include big halo and area about twice real. High level cuts thin lips and halo and gives about half. No single level works for all panels because gain and blur and tilt and noise shift. Counting pixels as area fails when far scratch has many dim pixels.

Optics preserve total brightness. Blur spreads but integral stays, so you can get true area back if you estimate energy belonging to main pit.

We check within three percent relative error. Naive thresholds are ten percent or more off.

Rules. Parse with struct only. Allowed imports are struct sys math random tempfile re. Do not use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath or any array or imaging or graph helper. Do not use eval exec compile __import__ chr. Do not use subprocess or system or popen or fork or walk or listdir or open of tests directory. Never mention tests directory or test_outputs or heldout or reference_volume or GEOM_TRUTH or geometric_truth inside solve.py. Your program must work on any temporary file path.

Last line print area mm2 as final token, like 12.345

