Pixel factory QA line checks OLED adhesive for trapped air voids using a new under-display IR scanner mounted on Android test rigs.

The rig dumps a raw backscatter cube from its VCSEL diffuser into app private storage via FileOutputStream (little-endian ByteBuffer, same path pattern as ARCore depth dumps you saw in other tasks). Each cube may contain:

- one main air-gap void (irregular bubble / delam pocket) that we need to measure
- a few far dust specks / fibre reflections that are NOT part of the bond void
- a flat DC background plus faint sensor noise
- anisotropic optical bleed: OLED stack diffuses IR wide in XY, bond is thin so Z bleed is narrow. A normalized Gaussian PSF with different XY vs Z sigmas does the spreading.

Your script must report the physical volume of the MAIN bond void in cubic mm.

Make a script at /app/solve.py . We run it like:

    python3 /app/solve.py /app/data/scene.obvl

The path to the cube is argv[1]. Sample at /app/data/scene.obvl for local dev. Hidden grading uses other OLED scans with different void sizes, emitter power, pitch, background.

Format .obvl is my own mini container, all little-endian:

- 0-3: ascii "OBVL" magic
- 4-7: u32 version = 1
- 8-11: u32 dtype code: 2 means little-endian int16, 16 means little-endian float32
- 12-23: 3x u32 nx, ny, nz voxel counts, total = nx*ny*nz
- 24-35: 3x f32 sx, sy, sz mm per voxel, anisotropic, read from header per file, do not assume same across files
- 36-39: u32 data_offset where payload starts (usually 64)
- payload: nx*ny*nz values of declared dtype, x fastest, index = x + nx*(y + ny*z)

Content: void interior is bright saturated plateau (air scattering strongest), thin delam fingers at edges partly filled -> dimmer intermediate values, border dim from partial fill + PSF smear. Threshold tricks fail: low threshold grabs huge smeared halo overestimates 70-120%, high threshold misses thin fingers underestimates 30-50%. No fixed threshold works because emitter power/background/pitch change per scan.

Physics that saves you: blur kernel is normalized, does not create/destroy photon counts, only spreads them. True geometric voxel count is:

    void_voxels = sum( background_subtracted_intensity over void + surrounding halo ) / plateau_amplitude

Plateau = concentration where IR most saturated (interior). Use largest-mass 26-connected component above noise to drop dust specks (far tiny bright blobs). Then grow slightly to include faint halo until surrounding shell mean falls back near noise level.

Print final volume mm3 as last whitespace token on stdout (float). Example output: "123.456" . Grading tolerance 3% on hidden OBVLs.

Constraints: parse binary yourself via struct. BANNED: numpy, scipy, skimage, cv2, PIL/Pillow, networkx, igraph, imageio, pandas, torch, tensorflow, subprocess, importlib, runpy, ctypes, socket, multiprocessing, glob. BANNED calls: eval, exec, compile, __import__, os.system, os.popen, os.exec, os.walk, os.listdir, os.scandir, pty. Also banned: reading /tests folder, openingheldout, importing test_outputs. Use stdlib only.

We grade by recomputing volume independently in pure stdlib via intensity conservation with a different robust heuristic, so memorizing sample numbers fails.
