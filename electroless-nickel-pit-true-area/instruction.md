I work on the plating line for automotive pin connectors. We plate electroless nickel phosphorus, Ni-P, about twelve microns thick on copper pins. Sometimes hydrogen bubbles sit on the surface during plating and block deposition, leaving a tiny pit that goes down to copper. In salt spray that pit turns into red rust and we fail the customer.

We check panels with a Bruker Contour GT-X white light interferometer. It measures surface height. The optics lie. The objective has an Airy disk, the stage shakes a little while scanning, and the fringe envelope is noisy. Together they smear a small deep pit into a wide shallow dish. On the screen a pit that is really round and deep looks like a big soft halo. We need the true area in square millimeters, not the blurry dish size.

You must write the tool.

Save it as /app/solve.py. We run python /app/solve.py with the scan file path as argument and we take the last word printed as your answer.

We give you one map to develop with at /app/data/scene.enpp. You can open it while coding. Hidden grading uses completely different maps you have never seen, with different panel sizes, pixel pitch, nickel brightness, pit depth, blur width, background tilt, and noise. They come as random temporary files. Do not hardcode numbers from the example. If you hardcode the sample area you will fail hidden tests.

File type is .enpp, our own small format for nickel pits, all little endian.

First four bytes are ASCII letters ENPP.
Next four bytes are version uint32, currently one.
Next four bytes are dtype code uint32. Two means each pixel is int16, sixteen means float32.
Next eight bytes are two uint32 values nx ny, number of pixels along x and y.
Next eight bytes are two float32 values sx sy, millimetres per pixel along x and y. They change per file, you must read them, they are anisotropic.
Next four bytes are uint32 offset where pixel data starts.
After that offset there are nx times ny samples in the announced dtype, x moves fastest, so index equals x plus nx times y. Background nickel is bright, pits are dark, we flipped during export so pits appear bright.

What is actually inside. Each file contains one main plating pit that we grade. It is roundish but has two thin undercut lips on the left and right where the bubble foot was pinned. Those lips are part of the true pit, even though they may appear faint after blur due to partial pixel coverage. There are also sometimes one or two tiny bright specks far away from the main pit, from dust particles or tiny polish scratches, and occasionally a broad shallow scratch far from the main pit that spans many pixels but has low total brightness. Those artefacts must be ignored. The true pit is the dominant bright region.

Why simple counting fails. If you take a low brightness level you include the big optical halo around the pit and you get roughly double the real area, sometimes more. If you take a high brightness level you cut off the thin lips and the faint halo and you get about half the real size. No single fixed level works for all panels because plating bath age, gain, thickness, blur width, background tilt, and noise change. Counting bright pixels as area breaks when a far scratch has many dim pixels.

Blur keeps energy. The lens spreads light but does not create or destroy light. Under a normalized blur the total integrated bright residual is preserved even though apparent area inflates. That is the invariant you need. True area can be recovered if you can estimate how much excess brightness belongs to the main pit.

We grade at three percent relative error. Simple thresholds are ten percent or more off.

Implementation rules. Parse bytes yourself with struct only. Allowed imports are struct sys math random tempfile re. Banned modules are numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath and any array or imaging or graph helper. Banned calls are eval exec compile import with double underscores and chr. Do not use subprocess or os dot system popen exec fork walk listdir scandir open or pty or importlib runpy ctypes or any directory listing. Do not hide paths with chr or bytes fromhex or base64 or b64decode or bytearray tricks. Never open or list the tests directory and never mention test_outputs heldout reference_volume GEOM_TRUTH geometric_truth inside your solve.py. Your program must work on any temporary file path, not a hardcoded path.

At the end print area in square millimeters as last word. Example final line 12.345 as area.
