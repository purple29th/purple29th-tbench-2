Hey, our on-device depth sensor (ToF, like ARCore) saves a small 3D scan of whatever is in front of the camera. Write a Python script at /app/solve.py that reads one of these scans, located at /app/data/scene.avol, and reports the physical volume of the scanned object as a single value in cubic millimetres.

Run it as:

    python3 /app/solve.py <path-to-volume>

The path is the first argument; we test your script on additional scans you have not seen. Print the object's volume in cubic millimetres as the final number on stdout.

In a scan the object shows up as a bright region (high-intensity voxels) sitting in mostly empty, low-intensity space. The header records the size of a single voxel in millimetres along each of the three axes.

The .avol format is little-endian:

    offset  0 : 4 bytes  magic, the ASCII "AVOL"
    offset  4 : uint32   version (currently 1)
    offset  8 : uint32   dtype code: 2 = signed int16, 16 = float32
    offset 12 : uint32   nx
    offset 16 : uint32   ny
    offset 20 : uint32   nz
    offset 24 : float32  sx   voxel size in mm along x
    offset 28 : float32  sy   voxel size in mm along y
    offset 32 : float32  sz   voxel size in mm along z
    offset 36 : uint32   data_offset (byte offset where the voxel data begins)
    then, starting at data_offset: nx*ny*nz voxel intensities of the given dtype,
    stored with x varying fastest, then y, then z
    (the intensity at (x, y, z) is element  x + nx*(y + ny*z)).

There is a sample scan at /app/data/scene.avol to develop against.

Parse the file yourself from the raw bytes. You may not use numpy, scipy,
scikit-image, OpenCV, PIL/Pillow, networkx, igraph, or any other array / imaging
/ graph library, and you may not shell out (no subprocess, os.system/os.popen,
__import__/importlib). Use only the Python standard library (e.g. open(...).read()
and struct).

We grade by running your script on several scans you have not seen.
