# sintered-silver-die-attach-void-subvoxel-volume

Power electronics QA: X-ray nano-CT of sintered silver die attach for SiC modules. Solvent outgassing voids appear as bright clouds due to focal spot and scintillator blur that conserves energy. Task asks for true geometric void volume in mm3 from custom .ssdv binary.

## Format
- magic SSDV, little-endian, version uint32, dtype uint32 (2=int16, 16=float32), nx ny nz uint32, sx sy sz float32 mm/voxel anisotropic, data_offset uint32, then nx*ny*nz voxels x-fastest.

## Difficulty
Hard - requires background median/MAD, largest-mass 26-connected component, plateau top-K, adaptive halo growth. Threshold counting fails 2x over / 0.5x under.

## Grading
3% relative tolerance via runtime-generated heldouts with geometric truth.
