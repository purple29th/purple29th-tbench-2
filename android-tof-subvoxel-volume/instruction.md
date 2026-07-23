Read a ToF depth scan and print the volume of the scanned object in cubic millimetres.

Write a Python script at /app/solve.py. Run it as:

    python3 /app/solve.py <path-to-volume>

The scan path is the first argument. Print the volume as the last number on stdout. We test on scans you have not seen. A sample scan sits at /app/data/scene.tvol.

How the sensor works: every voxel stores an intensity for how much of that voxel the object fills. A voxel fully inside reads a peak value; a voxel only partly filled reads less. The optics also blur each reading into nearby voxels, so the object shows up bright with soft edges. There is a flat background level plus faint noise on every voxel, and a few small stray bright specks may sit away from the object. Voxel size in mm differs per axis and per scan, and it is stored in the header.

The .tvol format is ours. Little endian, fixed header: a 4 byte magic TVOL, a uint32 version (1 for now), a uint32 dtype code (2 means int16, 16 means float32), then nx, ny, nz as uint32, then sx, sy, sz as float32 giving mm per voxel on x, y, z, then a uint32 data_offset marking where the voxel data starts. After that come nx*ny*nz intensities of that dtype in x fastest order, so voxel (x, y, z) sits at index x + nx*(y + ny*z).

Parse the bytes yourself. No numpy, scipy, scikit image, opencv, pillow, networkx, igraph, or any other array, imaging, or graph library, and no shelling out (subprocess, os.system, os.popen, __import__, importlib). Standard library only.

We grade by running your script on scans you have not seen.
