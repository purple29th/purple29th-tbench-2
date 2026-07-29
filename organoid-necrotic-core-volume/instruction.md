I have a set of 3D microscopy volumes that store dead cell signal inside a tissue block. Each volume is saved in my own binary format with extension .oncr. The signal comes from propidium iodide that marks dead nuclei. The brightest part is in the middle where staining saturates and looks flat. Near the edge the signal is weaker because voxels are only partly filled and also because light scatters in tissue and the microscope PSF smears everything. So the raw image looks much larger and fuzzier than the real dead region. There is also a fairly uniform background glow plus camera noise. A few volumes contain isolated bright dots far from the main region. Those dots are just debris from dying cells that detached and should not be counted.

I need a small tool that reads one of those files and outputs the true volume of the main dead region in cubic micrometers. The true size matters for my downstream analysis and my current brightness cutoff approach is not accurate at all.

Make a file at /app/solve.py. When I run python /app/solve.py <scan_path> I will look at the last word printed on stdout and treat it as the volume.

You can test locally with /app/data/scene.oncr. Grading uses other files you have never seen with different sizes, voxel pitch, brightness, amount of scatter, and background levels. Do not hardcode any numbers from the example file. Your code must work for any path given as first argument.

How .oncr files are laid out. All numbers are little endian.

* At byte zero there are four ASCII bytes ONCR.
* At byte four there is a uint32 version.
* At byte eight there is a uint32 dtype code. Value 2 means int16 voxels, value 16 means float32 voxels.
* At byte twelve there are three uint32 numbers nx ny nz that tell how many voxels along each axis.
* At byte twenty four there are three float32 numbers sx sy sz that tell micrometers per voxel along each axis. This changes per file so you must read it.
* At byte thirty six there is a uint32 data offset that tells where voxel data starts.
* After that offset there are nx times ny times nz voxel values in the dtype announced. Order is x fastest, so position x y z maps to index x + nx * (y + ny * z).

What is inside the volume. One main solid dead core plus maybe a few far dots. The main core is the one I care about. You should keep the largest bright component by total photon excess, not by voxel count, using 26 neighbour connectivity. This isolates the core from far debris.

Why simple brightness counting does not work for me. If I include everything above a permissive level I also include the scattered halo and my volume ends up eighty to one hundred thirty percent too large. If I use a strict high level I lose the thin protrusions that never reach high brightness and I end up thirty to fifty percent too small. No single level works for all files because brightness, tissue clarity, scatter width and background shift between batches. Counting bright voxels is not the right clue. The clue is total photon content.

Scatter and blur move photons around but the total number of photons is conserved. That lets you recover true size even though the image looks smeared, provided you handle a few things correctly. You need to estimate the background level without letting the bright core bias you. You need to estimate the true saturated PI level from the most concentrated part, not just the raw maximum which is noisy. You need to include the faint halo around the core until its mean drops to noise floor, but you must not grow into far debris. Those steps are where naive methods fail.

Grading asks for three percent accuracy. My naive counts are far outside that. Only a method that uses photon conservation together with robust debris removal and halo handling gets inside tolerance.

Implementation rules. You must parse the binary yourself using only the Python standard library. You may use struct sys math random tempfile re. The following are forbidden and will cause test_from_scratch to fail. numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath plus any other array imaging or graph library. Forbidden calls are eval exec compile __import__ chr. Forbidden runtime tricks are subprocess os.system os.popen os.exec os.fork os.walk os.listdir os.scandir os.open pty importlib runpy ctypes any filesystem listing, and any tricks that hide paths using chr bytes.fromhex base64 b64decode bytearray bytes list tricks or building paths via concatenation. Do not try to open or list /tests and do not mention test_outputs heldout reference_volume _gen GEOM_TRUTH or geometric_truth in your solver file. The solver must work on random temporary files, not on hardcoded paths.

Output the volume in cubic micrometers as the last token on stdout.
