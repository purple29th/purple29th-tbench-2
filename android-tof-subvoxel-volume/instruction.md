You need to make /app/solve.py. It gets one argument - path to a .tvol scan - and has to print the scanned object's volume in cubic mm. The volume must be the last number on stdout.

For local dev use /app/data/scene.tvol. Final scoring uses scans you have not seen, so generic handling is required. Invocation is:

python3 /app/solve.py <path-to-scan>

Our ToF depth camera writes a custom binary format. All numbers are little endian. Layout:

- 0..3 : ascii "TVOL"
- 4 : uint32 version
- 8 : uint32 dtype code. 2 = int16 voxels, 16 = float32 voxels
- 12 : three uint32 nx ny nz - volume dimensions
- 24 : three float32 sx sy sz - voxel size in mm for x,y,z
- 36 : uint32 data_offset - byte offset where voxel data starts

After data_offset there are nx*ny*nz values of type given by dtype, x varies fastest. So voxel (x,y,z) linear index is x + nx*(y + ny*z).

What you see in the volume: object is bright with soft blurred border. Per-voxel value encodes how much that voxel is filled - interior voxels sit near a high plateau peak, voxels cut by object surface are lower, optics smear that signal into neighbours because of point spread. There is a flat background/DC floor plus per-voxel noise. Some scans have a few small isolated bright specks far from main object - those are artefacts and must not be counted. sx sy sz are anisotropic and differ scan to scan, so always read them.

Rules: parse bytes yourself, stdlib only. Don't rely on numpy, scipy, scikit-image, opencv, pillow, networkx, igraph, imageio, pandas, torch, tensorflow or any array / imaging / graph helper. Don't shell out and don't do dynamic imports. That means no subprocess, no os.system / os.popen / os.exec, no __import__, no importlib, no runpy, no ctypes, no eval/exec.

On stdout print the object's volume in mm^3. Ensure the very last token is the numeric volume - we will parse it. The evaluator will run your script on held-out scans.
