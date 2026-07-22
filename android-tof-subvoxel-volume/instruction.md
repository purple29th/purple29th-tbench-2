Our on-device depth sensor (a ToF camera, like ARCore) saves a small 3D scan of whatever is in front of the camera. Write a Python script at /app/solve.py that reads one of these scans, located at /app/data/scene.tvol, and reports the physical volume of the scanned object as a single value in cubic millimetres.

Run it as:

    python3 /app/solve.py <path-to-volume>

The path is the first argument; we test your script on additional scans you have not seen. Print the object's volume in cubic millimetres as the final number on stdout.

How the sensor works: for each voxel it records an intensity that reflects how much of that voxel the object fills. A voxel sitting fully inside the object reads a peak intensity; a voxel the object only partially covers reads proportionally less. The sensor optics also spread each reading across neighbouring voxels, so the object shows up as a bright but soft-edged region. On top of this sits a constant background level plus faint per-voxel noise, and the scene may contain a few small, isolated bright specks (sensor artefacts) away from the object. The header records the size of a single voxel in millimetres along each of the three axes.

The .tvol format is one we put together ourselves, so here's how it's laid out. It's little-endian with a fixed-size header: a 4-byte magic "TVOL", a uint32 version (1 for now), a uint32 dtype code (2 means signed int16, 16 means float32), then the dimensions nx, ny, nz as uint32s, then the voxel sizes sx, sy, sz as float32s in millimetres along x, y and z, and finally a uint32 data_offset marking the byte where the voxel data begins. From there it's nx*ny*nz intensities of that dtype, stored x-fastest then y then z, so the voxel at (x, y, z) sits at index x + nx*(y + ny*z).

There is a sample scan at /app/data/scene.tvol to develop against.

Parse the file yourself from the raw bytes. You may not use numpy, scipy,
scikit-image, OpenCV, PIL/Pillow, networkx, igraph, or any other array / imaging
/ graph library, and you may not shell out (no subprocess, os.system/os.popen,
__import__/importlib). Use only the Python standard library (e.g. open(...).read()
and struct).

We grade by running your script on several scans you have not seen.
