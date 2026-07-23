hey so we have been labeling tumors with gold nanoclusters and imaging them under confocal fluorescence. the gold makes the tumor really light up but there is a problem. everywhere you look there is light spread. the microscope has this airy disk point spread thing that smears the concentrated gold signal all around so the tumor looks bigger and fuzzier than it really is.

i need a script that figures out the true physical volume of the gold labeled tumor. not the smeared bright blob but the real size. and precision matters. if you are off by even a few percent you misestimate dose.

make a file called solve dot py and put it in the app folder. we will call it as python app solve py with path to a scan as first argument. whatever you print last word we take as volume in cubic mm.

we give you one scan to develop on. it is named scene dot gvol inside data folder that is inside app. grading uses other scans you never saw with different sizes spacings brightness and even different gold concentrations and different voxel sizes. do not hardcode numbers from example.

what is gvol. its our own small binary for gold volumes. all numbers little endian.

file starts with four letters G V O L as ascii.

next four bytes version unsigned thirty two bit little endian.

next four bytes dtype code unsigned thirty two bit little endian. two means voxels are sixteen bit signed int. sixteen means thirty two bit float.

next twelve bytes three unsigned thirty two bit counts for how many voxels along each axis. think width height depth but we call them nx ny nz historically.

next twelve bytes three thirty two bit floats that tell how big one voxel is in mm along each axis. think mm per voxel. historically called sx sy sz. they are anisotropic and change every file so you must read them from header.

next four bytes unsigned thirty two bit data offset where voxel data starts.

after that you have nx times ny times nz voxel values in announced dtype. x is fastest. so voxel x y z lives at index x plus nx times bracket y plus ny times z bracket.

what is inside. one main solid tumor labeled with gold. gold makes it super bright inside, almost flat high intensity where concentration is saturated. but at the border voxels are only partly filled so dimmer. and because airy psf spreads, that bright interior bleeds out into neighbors making a halo that is still bright but should not be counted as full voxels. also there is flat autofluorescence background plus camera noise everywhere. some scans have one or two tiny isolated bright specks far away from main tumor, they are gold dust artefacts, you must ignore them and only keep the main tumor that is one big connected mass.

now why this is tricky and why every agent will find it hard to be precise. anywhere you threshold you get light everywhere so if you just pick a brightness cutoff and count voxels you will never get right volume. low cutoff makes tumor look huge because halo included. high cutoff makes you miss thin infiltrating strands that never get bright enough because they are only partly filled. the scans are intentionally such that no fixed cutoff works across files. the images are all blurry and the most useful information is not the number of bright voxels but where light is most concentrated. the real tumor core is where gold is most concentrated and that concentration is roughly flat. but you never see that flat value directly because blur plus noise hide it. you have to infer it.

so you need to think about what blur does. it spreads energy around but it does not create or destroy light. that physical fact is what makes precise volume possible at all. but figuring out how to use it, how to separate main tumor from specks, how to estimate background without bias from tumor itself, how to estimate the true concentrated brightness without being fooled by noise, and how to decide how far the faint halo extends without merging into far specks, that is the hard engineering you must do.

if you rely on simple tricks you will be off by twenty to one hundred thirty percent. we grade at three percent tolerance so only a genuine precise method will pass.

you must parse bytes yourself with only stdlib like struct. do not use numpy scipy scikit image opencv pillow networkx igraph imageio pandas torch tensorflow or any array image graph library. do not use subprocess os system popen exec import tricks like double underscore import importlib runpy ctypes eval exec compile shell stuff. do not try to read tests folder or list filesystem to find hidden scans.

at the end print volume in mm3 as last word on stdout.
