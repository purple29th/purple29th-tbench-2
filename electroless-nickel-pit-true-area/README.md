# electroless-nickel-pit-true-area

Plating QC: white light interferometer of electroless nickel pits from hydrogen bubbles. Lens PSF plus stage vibration creates normalized blur conserving counts but inflating apparent pit area.

Format: magic ENPP, little endian, version uint32, dtype uint32 (2=int16,16=float32), nx ny uint32, sx sy float32 mm per pixel anisotropic, data offset uint32, then nx*ny pixels x fastest.

Grading: 3% relative tolerance via runtime generated heldouts with geometric truth.
