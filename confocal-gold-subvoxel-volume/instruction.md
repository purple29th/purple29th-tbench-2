hey i am working in the wet lab. we tag tumors with gold nanoclusters so they glow under confocal. problem is gold glows so strong that light is everywhere. airy disk spreads concentrated glow all over so tumor looks bigger than it is and edges are all fuzzy.

need a program that tells true physical size of gold labeled tumor in cubic mm. not smeared blob.

make file named solve dot py and drop in app folder. we run it as python app solve py with scan path as arg. last word printed is taken as volume.

you have one example to try. name is scene dot gvol inside data folder which is inside app. hidden grading uses other files you never saw with different sizes spacings brightness gold amount and voxel sizes. do not hardcode numbers from example like counts or intensities.

what is gvol. our own tiny binary for gold volumes. everything little endian least significant byte first.

starts with four letters G V O L ascii.

next four bytes version as unsigned thirty two bit little endian.

next four bytes dtype code unsigned thirty two little endian. two means int16 voxels. sixteen means float32 voxels.

next twelve bytes three unsigned counts of voxels per axis width height depth historically nx ny nz.

next twelve bytes three float32 values saying mm per voxel per axis historically sx sy sz. they change every file anisotropic so read them.

next four bytes unsigned data offset where voxel block starts.

after offset there are nx times ny times nz values in that dtype. x fastest so index for x y z is x plus nx times bracket y plus ny times z bracket.

inside is one main solid tumor that glows because gold. center is flat bright where concentration saturated. border voxels dimmer because only partly filled and smeared by airy. plus flat background autofluorescence plus noise everywhere. some scans have one or two tiny bright specks far away from tumor they are gold dust artefacts ignore them keep only main connected tumor mass.

why this is hard for every agent. you look at image and see light everywhere. if you pick brightness cutoff and count voxels you will never be precise. low cutoff counts huge halo and overcounts eighty to one hundred thirty percent. high cutoff misses thin strands that never get bright enough due to partial filling and undercounts thirty to fifty percent. scans were made so no fixed cutoff works across files. all images blurry and best clue is not how many bright voxels but where gold is most concentrated. true core has almost flat concentration but you never see it directly because blur and noise hide it.

blur spreads energy around but does not create or destroy light. that physics is why precise volume is possible at all. but using it properly, separating main tumor from far specks, estimating background without being biased by tumor itself, figuring out true concentrated brightness without being tricked by noise, deciding how far faint halo goes without merging into specks, that is hard engineering you must solve.

if you use simple tricks you will be off by large margin. we grade at three percent tolerance so only genuinely precise method passes.

parse bytes yourself using only stdlib like struct. do not import numpy scipy scikit image opencv pillow networkx igraph imageio pandas torch tensorflow or any array image graph library. do not use subprocess os system popen exec dynamic import tricks like double underscore import importlib runpy ctypes eval exec compile shell tricks. do not try to read tests folder or list filesystem.

final step print volume mm3 as last word on stdout.
