# hot-rolled-sulfide-stringer-length

I check hot rolled steel plates for manganese sulfide stringers that cause lamellar tearing during welding. The plate is inspected with fluorescent magnetic particle that makes MnS glow, stored as .strg with magic STRG. Scintillator diffusion plus lens PSF smears the glow far beyond true sulfide.

Why level counting fails. Generous level includes whole aureole and nearly doubles length. Strict level loses thin tips and loses third to half. Background gain and scatter vary per coil.

Energy preservation saves us. Optics do not create photons, they only move them. So sum of background removed glow over stringer plus skirt divided by core level gives true voxel count.

A correct program must read header with data offset not hardcoded, get background from seventy percent lower median and noise from lower half MAD, seed bright voxels above four sigma and grow twenty six connected blobs, keep elongated stringers along rolling direction where longest at least eight and more than one point six times shortest and drop compact MnS dots, get core level via three by three by three smoothed top four mean, expand outward until mean shell drops to noise floor while skipping artefacts, compute voxel count then volume via sx sy sz then length via cross section zero point one eight mm2 so length equals volume divided by zero point one eight.

Files:
* /app/solve.py you write, last token is length in mm
* /app/data/scene.strg sample
* Dockerfile installs pytest and copies sample
* tests secure verifier generates at runtime with random names

Pass when error under three percent on cases including speck heavy and dot heavy. Naive threshold fails. Global without filter fails speck heavy. Largest mass without shape fails dot heavy.

No numpy scipy etc, stdlib only.

Author Tosin Daniel Jimoh purple29th at meta.com
