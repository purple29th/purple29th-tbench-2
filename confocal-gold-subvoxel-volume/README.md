# codimango/confocal-gold-subvoxel-volume

Sister task to `android-tof-subvoxel-volume` and `mri-volume-calc` but with confocal gold nanocluster fluorescence cover story.

The agent writes from-scratch Python (`/app/solve.py`, stdlib only) that reads custom binary `.gvol` (magic GVOL) and reports physical volume mm^3 of gold-labeled tumor.

Core difficulty same as ToF version: bright blob with Airy disk PSF blur spreads light everywhere, thresholding fails 20-130%. Must find most concentrated area (plateau amplitude via 3x3x3 mean filter peak) and integrate background-subtracted intensity over object+halo (intensity conservation).

Gold context makes it more intuitive: gold makes tumor concentrated bright, but microscope smears light, so you have light everywhere and need to find where concentration is highest for precise volume.

Grading at 3% tolerance, held-out scans 3977, 3983, 4428 mm3 vs sample 3206 mm3.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
