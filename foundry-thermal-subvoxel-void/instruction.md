hey i am in foundry checking turbine blades made by laser powder bed fusion. after print we flash heat the part and watch with mid wave infrared. pores trap heat and glow but heat spreads everywhere. thermal diffusion plus lens gives point spread that smears hot glow all over so void looks bigger fuzzy than real.

i need program that tells true physical size of internal void in cubic mm not smeared thermal blob. precision matters for fatigue life.

make file named solve dot py inside app folder. we call it as python app solve py with scan path as argument. last word printed taken as volume.

you get one example to try named scene dot tiv inside data folder that is inside app. hidden grading uses other files you never saw with different sizes spacings brightness metal conductivity and voxel pitch. do not hardcode numbers from example.

what is tiv. our own small binary for thermal ir void volumes. everything little endian.

file starts with four ascii T I V R.

version is next four bytes unsigned thirty two little endian.

dtype code next four bytes unsigned thirty two little endian. two means int16 voxels. sixteen means float32 voxels.

next twelve bytes are three unsigned counts of voxels per axis width height depth historically nx ny nz.

next twelve bytes are three float32 values mm per voxel per axis historically sx sy sz. they change every file so read them.

next four bytes unsigned data offset where voxels start.

after offset you have nx times ny times nz values in announced dtype. x fastest so index for x y z is x plus nx times bracket y plus ny times z bracket.

inside is one solid hot void glowing because heat trapped. center flat hot where temperature saturated. border dimmer partly filled smeared by thermal diffusion. flat ambient background plus sensor noise. some scans have one or two tiny hot specks far away spatter artefacts ignore keep only main connected hot mass twenty six neighbours.

this is tricky and every agent will find it hard to be precise. threshold counting never precise. low cutoff includes huge halo overcounts eighty to one hundred thirty percent. high cutoff misses thin cracks that never get hot enough undercounts thirty to fifty percent. no fixed cutoff works across files. images blurry best clue is where heat is most concentrated not how many bright voxels. true core flat but hidden by diffusion noise.

blur spreads energy but does not create or destroy heat. that physics makes precise volume possible. but using it means separating main void from far specks estimating background without bias from void itself figuring true concentrated temperature without noise trick and deciding how far faint halo goes without merging specks. that is hard.

simple tricks off large margin. grade at three percent tolerance only genuine precise method passes.

parse bytes yourself only stdlib like struct. banned: numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io any array image graph helper. banned runtime tricks: subprocess os.system os.popen exec double underscore import importlib runpy ctypes eval exec compile shell filesystem listing glob multiprocessing socket pathlib os io chr bytes bytearray posixpath ntpath genericpath. also do not open / read tests directory.

print volume mm3 as last word.
