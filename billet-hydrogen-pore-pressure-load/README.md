# billet-hydrogen-pore-pressure-load

I look after continuous cast aluminum billets that go into extrusion for structural parts. Hydrogen from humidity and melt handling diffuses into billet and forms round sealed pores that are pressurized. Under extrusion they open as blisters that fail surface QA. I need to know internal gas pressure in kilopascals to rank billets for degas.

Imaging uses X-ray fluorescence that lights up hydrogen rich regions. Data is custom binary .hprr with magic HPPR. Diffusion in scintillator plus lens point spread smears the pore glow far beyond true metal core. Task asks for pressure in kPa, not just volume.

Why simple brightness cut is hopeless. If I am generous I include whole aureole and my volume balloons and my pressure estimate collapses because pressure is constant divided by volume. If I am strict I lose thin feathered pore edges and I underestimate volume and my pressure spikes. Each file has different background, gain, scatter width.

Energy preservation saves us. Optics do not create fluorescence, they only move it. So sum of background removed glow over pore plus its faint skirt divided by true interior level gives true voxel count even though blurred. Then volume via sx sy sz from header and pressure via ideal gas.

How evaluation punishes shortcuts. Volumes contain round hydrogen pores that are near spherical and must be counted, plus elongated manganese sulfide stringers that are long along casting direction that must be ignored, plus window dust balls far away. Round versus elongated is opposite to many older tasks that kept elongated. Here we keep round where longest at most two point five times shortest and at most twenty eight and drop stretched stringers where longest at least twelve and more than three times shortest which become twenty by six by six after smear, while a five by five by five pore smears to about twenty by fifteen by ten and still passes round test. That inversion makes reskin detection hard. Some volumes have two separate round pores far apart that all count and contribute to total volume before pressure conversion, so keeping only biggest fails.

A correct solver must read header with data offset not hardcoded, get border background from median and noise from lower half MAD, seed bright voxels above four sigma and grow twenty six connected blobs, keep round pores via roundness test and drop stretched stringers, get core level via three by three by three smoothed top four raw fallback, expand outward until mean shell drops to noise floor while skipping artefact voxels, compute voxel count then volume then pressure as constant seven hundred eighty divided by volume.

Files:
* /app/solve.py you write, last token is pressure kPa
* /app/data/scene.hprr sample around fourty eight kPa example
* Dockerfile installs pytest and copies sample
* tests secure verifier generates at runtime with random temp names like input_9f3a.hprr

Pass when error under three percent on cases including speck heavy where large window dust contributes more than three percent extra glow and stringer heavy where elongated stringers together outweigh round pores.

No numpy scipy etc, stdlib only struct sys math.

Author Tosin Daniel Jimoh purple29th at meta.com
