We have silver sinter die attach voids that make power modules fail thermal.

I am on the power module line. We mount SiC MOSFETs on DBC copper with silver sinter paste. After sinter, trapped solvent leaves sealed bubbles between die and substrate. Those bubbles raise thermal resistance and parts overheat in power cycling.

We check with X-ray. Picture lies. Tube spot and scintillator and scatter in silver spread a small bubble into a big fuzzy cloud. What is really compact looks like huge bright halo on monitor. Need true bubble volume mm3, not cloudy size.

Write a program.

Put it at /app/solve.py. We call python /app/solve.py /path/to/file.ssdv and we read last token you print as answer.

For local dev we left one scan at /app/data/scene.ssdv you can open. Hidden tests use totally different scans you never saw, different die sizes, voxel pitch, brightness, blur, background, noise. Do not hard code from example.

File is custom binary SSDV, little endian. Magic SSDV, version, dtype, dims nx ny nz, spacing sx sy sz mm per voxel anisotropic you must use, data offset, then voxel values x fastest so index is x plus nx times y plus nx times ny times z. We flipped so bubbles look bright.

Inside each file there is one main bubble we score. It is mostly round but has thin vent legs where gas tried to escape to die edge, those legs count as part of bubble even though they look faint after smear. Sometimes there are one or two tiny bright dots far away from main bubble from organic residue or tiny paste clumps. Ignore those, main is dominant bright blob.

Fixed level does not work. Low level includes big halo and volume about double real. High level cuts thin legs and halo and gives about half. No single level works for all lots because paste lot and blur and noise shift. Counting voxels as volume fails when far dot has many pixels.

Optics keep total counts. Blur spreads but integral stays, so true volume recoverable via energy.

We check within three percent relative error. Naive thresholds far outside.

Rules. Parse with struct only. Allowed imports struct sys math random tempfile re. Do not use numpy scipy skimage cv2 PIL etc. Do not use eval exec compile or chr tricks. Do not open tests directory. Work on any temp file path.

Last line print volume mm3 as final token.
