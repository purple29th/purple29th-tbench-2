Power module failure from silver sinter outgassing – implement /app/solve.py

Production: SiC MOSFET die attach to copper DBC via pressure silver sintering. Paste contains solvent; incomplete burnout leaves trapped gas. Result is sealed cavity at interface that increases thermal resistance, parts fail in power cycling.

Inspection: nano-focus CT at 160kV. Dense silver/copper scatter broadens signal – compact cavity looks like extended cloud with thin channels reaching die edge. Goal is true cavity volume mm3, not cloud extent.

Usage: python /app/solve.py /path/file.ssdv → final token volume. Example file /app/data/scene.ssdv available; evaluation uses unseen volumes with varied dimensions, anisotropic voxel size sx sy sz, gain, blur, offset, noise. Must generalize.

Encoding: file type SSDV, little-endian. Header: 4B magic SSDV, u32 version, u32 dtype (2=int16,16=float32), three u32 dims nx ny nz, three f32 spacings sx sy sz mm per voxel, u32 data offset, then nx*ny*nz values. Voxels are x-fastest: index = x + nx*(y + ny*z). Spacings and offset vary per scan and must be read.

Per scan, one cavity to measure: near-spherical with narrow vent paths to edge that are faint after convolution but belong to cavity. Extraneous signals: remote isolated bright spots from organics/paste – ignore; they hold less integrated intensity than true cavity despite possibly many voxels.

Why thresholding fails: low cut captures cloud → ~2× volume, high cut drops vents → ~0.5×. No universal cut as material and imaging vary.

Principle: convolution kernel is normalized, so total sum is invariant – volume = total base-subtracted energy / robust plateau intensity * voxel volume sx*sy*sz. Estimate plateau as robust interior brightness, e.g. 3x3x3 smoothed top-K mean of the largest-mass 26-connected component to avoid single-voxel spike.

Within 3% relative.

Implementation rules: only stdlib struct for parsing. Allowed imports: struct sys math random tempfile re. Forbidden: numpy, imaging, graph, os, io, pathlib, subprocess, socket, chr tricks, eval. No /tests access.

Output mm3.
