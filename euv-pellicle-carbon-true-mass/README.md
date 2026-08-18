# euv-pellicle-carbon-true-mass

I look after reticle pellicles in the EUV scanner fleet. The pellicle is a ten nanometer freestanding film that shields the reticle. Under thirteen point five nanometer light, residual hydrocarbons crack and plate as amorphous carbon veins that darken the film and raise temperature. My job uses fluorescence that makes carbon shine, stored as .epcm with four byte tag EPCM. Carrier scattering in the detector and the imaging lens spread the shine far beyond the true soot.

Why counting by brightness is hopeless. If I set a permissive level I pick up the whole skirt and my estimate nearly doubles. If I set a strict level I lose the hairline tips that never reach full brightness and I lose about a third to half. The background level, gain, and scatter width change every scan, so a single fixed level never works.

What saves us is energy preservation. The optics do not create fluorescence, they only relocate it. So adding up all background removed glow over vein plus its faint aureole and dividing by the true vein interior brightness gives true voxel count even though blurred.

How the hidden evaluation is built to punish shortcuts. Volumes contain long branching carbon veins that follow crazing lines on the membrane. Those are the only carbon that counts for replacement decision. There are also compact airborne fallout dots that are almost spherical and must be ignored, plus window dust balls far away. Veins are stretched, fallout is compact. I use bounding box to tell them apart, stretched when longest side at least eight and more than one point six times shortest.

A correct program must:
* read magic EPCM and parse little endian header with data offset not assumed sixty four
* estimate robust background and noise, isolate stretched veins from compact fallout and far dust
* estimate robust vein interior brightness that tolerates noise and thin tips without flat plateau
* collect faint halo out to noise floor without bridging into nearby artefacts
* turn integrated glow into voxel count, then into cubic millimeters with sx sy sz from header, then into micrograms with two point one microgram per cubic millimeter lab factor

Files you will see:
* /app/solve.py is what you have to write, last printed token is mass in ug
* /app/data/scene.epcm is an example you can open locally
* Dockerfile installs pytest and copies example
* tests generate new volumes at runtime in temp directories with random names like input_a3f9.epcm, truth computed geometrically outside sandbox

Pass when error under two percent on cases that include speck heavy where large window dust contributes more than three percent extra glow if not removed, and particle heavy where compact fallout dots outweigh thin vein tips. Whole stack energy sum fails speck heavy. Mass only without stretch test fails particle heavy.

Difficulty target in the lithography domain: oracle near one percent, fixed level zero, global without filter zero on speck heavy, expected gpt two of five, opus two of five, avocado zero to one of five.

No numpy scipy skimage cv2 PIL etc, only struct sys math random tempfile re.

Author Tosin Daniel Jimoh purple29th at meta.com
