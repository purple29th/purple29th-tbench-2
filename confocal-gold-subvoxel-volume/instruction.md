hey so we have been labeling tumors with gold nanoclusters and imaging them under confocal fluorescence. the gold makes the tumor really light up but there is a problem. everywhere you look there is light spread. the microscope has this airy disk point spread thing that smears the concentrated gold signal all around so the tumor looks bigger and fuzzier than it really is.

i need a script that figures out the true physical volume of the gold labeled tumor. not the smeared bright blob but the real size.

make a file called solve dot py and put it in the app folder. we will call it as python app solve py with path to a scan as first argument. whatever you print last word we take as volume in cubic mm.

we give you one scan to develop on. it is named scene dot gvol inside data folder that is inside app. grading uses other scans you never saw with different sizes spacings brightness and even different gold concentrations. do not hardcode numbers from example.

what is gvol. its our own small binary for gold volumes. all numbers little endian.

file starts with four letters G V O L as ascii.

next four bytes version unsigned thirty two bit little endian.

next four bytes dtype code unsigned thirty two bit little endian. two means voxels are sixteen bit signed int. sixteen means thirty two bit float.

next twelve bytes three unsigned thirty two bit counts for how many voxels along each axis. think width height depth but we call them nx ny nz historically.

next twelve bytes three thirty two bit floats that tell how big one voxel is in mm along each axis. think mm per voxel. historically called sx sy sz. they are anisotropic and change every file so you must read them.

next four bytes unsigned thirty two bit data offset where voxel data starts.

after that you have nx times ny times nz voxel values in announced dtype. x is fastest. so voxel x y z lives at index x plus nx times bracket y plus ny times z bracket.

what is inside. one main solid tumor labeled with gold. gold makes it super bright inside, almost flat high intensity plateau where concentration is saturated. but at the border voxels are only partly filled so dimmer. and because airy psf spreads, that bright interior bleeds out into neighbors making a halo that is still bright but should not be counted as full voxels. also there is flat autofluorescence background plus camera noise everywhere. some scans have one or two tiny isolated bright specks far away from main tumor, they are gold dust artefacts, ignore them by keeping only the biggest connected bright mass using twenty six neighbours.

now why precision is hard. if you threshold and count voxels you will be wrong no matter what threshold you pick. low threshold includes huge halo and you overcount by eighty to one hundred thirty percent. high threshold cuts away thin infiltrating strands of tumor that never reach plateau because of partial volume and you undercount by thirty to fifty percent. there is also light everywhere so you have to find where concentration is highest. the trick we learned from mri tumor work is that blur conserves total light. so total background subtracted intensity equals true filled voxel count times plateau amplitude. so true count equals sum of background subtracted signal over tumor plus its faint halo divided by plateau amplitude. then times sx sy sz for mm3.

so your steps should be something like estimate flat background. background dominates volume so median works. estimate noise via mad. subtract background. find bright region above noise. label twenty six connected components. keep one with biggest integrated mass not biggest voxel count to drop specks. then estimate plateau amplitude where gold is most concentrated. do not just take max voxel because noise makes it noisy. instead do three by three by three mean filter over that biggest mass and take average of top few filtered values, say top eight, that recovers interior.

then you need to capture halo that still carries gold signal. grow region outward shell by shell while mean of new shell still above noise floor. then sum residual over final grown region. divide by amplitude. times spacing.

that is where precision comes from. finding the most concentrated area is key. if you get amplitude wrong by ten percent volume wrong by ten percent. if you miss halo you undercount. if you include specks you overcount.

you must parse bytes yourself with only stdlib like struct. do not use numpy scipy scikit image opencv pillow networkx igraph imageio pandas torch tensorflow or any array image graph library. do not use subprocess os system popen exec import tricks like double underscore import importlib runpy ctypes eval exec compile shell stuff. do not try to read tests folder or list filesystem.

at the end print volume in mm3 as last word on stdout.
