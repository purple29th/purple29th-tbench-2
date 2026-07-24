hey i am in paper lab testing how ink spreads on porous filter paper. we drop one ink drop and it wicks everywhere. capillary plus lens gives point spread that smears dark ink all over so blot looks bigger fuzzy than real inked area.

i need program that tells true physical inked area in square mm not smeared blot. precision matters for quality.

make file named solve dot py inside app folder. we call it as python app solve py with scan path as argument. last word printed taken as area.

you get one example to try named scene dot inkb inside data folder that is inside app. hidden grading uses other files you never saw with different sizes spacings darkness paper porosity and pixel pitch. do not hardcode numbers from example.

what is inkb. our own small binary for ink blot area. everything little endian.

file starts with four ascii I N K B.

version is next four bytes unsigned thirty two little endian.

dtype code next four bytes unsigned thirty two little endian. two means int16 pixels. sixteen means float32 pixels.

next eight bytes are two unsigned counts of pixels per axis width height historically nx ny.

next eight bytes are two float32 values mm per pixel per axis historically sx sy. they change every file so read them.

next four bytes unsigned data offset where pixels start.

after offset you have nx times ny values in announced dtype. x fastest so index for x y is x plus nx times y.

inside is one solid ink blot because capillary. center flat dark where ink saturated. border dimmer partly filled smeared by diffusion. flat paper background plus noise. some scans have one or two tiny dark specks far away dust artefacts ignore keep only main connected blot mass eight neighbours.

this is tricky and every agent will find it hard to be precise. threshold counting never precise. low cutoff includes huge halo overcounts eighty to one hundred thirty percent. high cutoff misses thin feathered wicking that never gets dark enough undercounts thirty to fifty percent. no fixed cutoff works across files. images blurry best clue is where ink is most concentrated not how many dark pixels. true core flat but hidden by diffusion noise.

blur spreads energy but does not create or destroy ink. that physics is key to precise recovery despite smear. the PSF is normalized so some integral quantity is conserved even though ink looks smeared. think about what stays conserved when a normalized blur spreads a flat blot, and how you could use that conservation if you can estimate background and true darkness robustly. separating main blot from far dust specks and deciding how far faint halo goes is the hard part.

simple tricks off large margin. grade at three percent tolerance only genuine precise method passes.

parse bytes yourself only stdlib like struct and sys and math. allowed stdlib includes struct sys math os random tempfile re but not numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow subprocess socket multiprocessing glob pathlib importlib runpy ctypes. banned calls include eval exec compile __import__ chr getattr setattr. also banned is any filesystem inspection via os.system popen exec fork walk listdir scandir rglob glob() and any trick to hide paths using chr() bytes.fromhex base64 b64decode or obfuscation. do not open /tests folder and do not reference test_outputs heldout reference _gen scene.inkb /app/data GEOM_TRUTH geometric_truth. solver must be from scratch and work on random temp files, not hardcoded paths.

print area mm2 as last word.
