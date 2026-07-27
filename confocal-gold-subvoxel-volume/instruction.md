hey i am in wet lab tagging tumors with gold nanoclusters. gold makes tumor glow under confocal but light goes everywhere. airy disk point spread smears concentrated glow all over so tumor looks bigger fuzzy.

i need program that tells true physical size of gold labeled tumor in cubic mm not smeared blob. precision matters for dosing.

make file named solve dot py inside app folder. we call it as python app solve py with scan path as argument. last word printed taken as volume.

you get one example to try named scene dot gvol inside data folder that is inside app. hidden grading uses other files you never saw with different sizes spacings brightness gold amount and voxel pitch. do not hardcode numbers from example.

what is gvol. our own small binary for gold volumes. everything little endian.

file starts with four ascii G V O L.

version is next four bytes unsigned thirty two little endian.

dtype code next four bytes unsigned thirty two little endian. two means int16 voxels. sixteen means float32 voxels.

next twelve bytes are three unsigned counts of voxels per axis width height depth historically nx ny nz.

next twelve bytes are three float32 values mm per voxel per axis historically sx sy sz. they change every file so read them.

next four bytes unsigned data offset where voxels start.

after offset you have nx times ny times nz values in announced dtype. x fastest so index for x y z is x plus nx times bracket y plus ny times z bracket.

inside is one solid tumor glowing because gold. center flat bright where concentration saturated. border dimmer partly filled smeared by airy. flat autofluorescence background plus noise. some scans have one or two tiny bright specks far away gold dust artefacts ignore keep only main connected tumor mass twenty six neighbours.

this is tricky and every agent will find it hard to be precise. threshold counting never precise. low cutoff includes huge halo overcounts eighty to one hundred thirty percent. high cutoff misses thin strands that never get bright enough undercounts thirty to fifty percent. no fixed cutoff works across files. images blurry best clue is where gold is most concentrated not how many bright voxels. true core flat but hidden by blur noise.

blur spreads energy but does not create or destroy light. that physics makes precise volume possible. but using it means separating main tumor from far specks estimating background without bias from tumor itself figuring true concentrated brightness without noise trick and deciding how far faint halo goes without merging specks. that is hard.

simple tricks off large margin. grade at three percent tolerance only genuine precise method passes.

parse bytes yourself only stdlib like struct and sys and math and os and random and tempfile and re but not numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow subprocess socket multiprocessing glob pathlib importlib runpy ctypes. banned calls include eval exec compile __import__ chr getattr setattr. also banned is any filesystem inspection via os.system popen exec fork walk listdir scandir rglob glob() and any trick to hide paths using chr() bytes.fromhex base64 b64decode or obfuscation. do not open /tests folder and do not reference test_outputs heldout reference _gen scene.gvol /app/data GEOM_TRUTH geometric_truth reference_volume. solver must be from scratch and work on random temp files, not hardcoded paths.

print volume mm3 as last word.
