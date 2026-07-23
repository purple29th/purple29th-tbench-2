hey i have these scans from a time of flight sensor we built and i want you to measure the thing inside.

make a file called solve dot py and drop it in the app folder. we will run it like python with the file path to a scan as argument and we expect it to output a number that is the size in cubic mm. we only care about the last word it prints.

we give you one example scan to play with. its called scene dot tvol and lives in the data folder which itself is inside app. the real grading uses different files you have never seen so dont bake in any numbers from the example.

what is a tvol file. its our own tiny format. everything is little endian in there. start at zero. first four bytes should be the letters T V O L. then four bytes version little endian unsigned int. then four bytes dtype code little endian unsigned int. two means the voxels are sixteen bit signed ints. sixteen means thirty two bit floats. then twelve bytes that are three unsigned ints for nx ny nz how many voxels per axis. then twelve bytes that are three floats sx sy sz physical edge length of one voxel in millimeters per axis. then four bytes unsigned int data offset where the actual voxel data begins.

after that offset you have nx times ny times nz numbers in the dtype. order is x runs fastest. so to get x y z you compute x plus nx times open bracket y plus ny times z close bracket.

inside the volume there is a single solid piece that is bright. optics make it blurry so interior is flat high but near the border it gets dimmer because only part of voxel is filled and that brightness smears to nearby voxels. plus there is flat background plus little noise everywhere. sometimes there are one or two tiny bright dots far away they are junk you must ignore by keeping the biggest connected bright blob twenty six neighbours.

you cannot get correct size by just thresholding and counting. blur keeps total energy so you need to estimate background subtract it estimate peak interior value integrate background removed values over the object plus its halo and divide by peak and then times sx times sy times sz.

you have to read bytes yourself with only stdlib like struct. dont bring numpy scipy scikit image cv opencv pillow networkx igraph imageio pandas torch tensorflow or any array picture graph library. dont use subprocess os system popen exec tricks or dunder import importlib runpy ctypes eval exec compile shell stuff. dont try to open tests folder or list files to cheat.

final step output size in cubic mm as last word.
