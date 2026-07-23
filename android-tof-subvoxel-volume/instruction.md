i built a small depth camera rig that saves scans. i need to know how big the thing in front is in cubic mm.

there is a spot where your code should go. make a file named solve dot py inside app folder. we will run it like python app solve py with one argument which is path to a tvol scan. whatever you print last word we take as volume.

you have one file to test on locally. name is scene dot tvol inside data folder which is inside app. hidden tests use other files you never saw with different sizes brightness and voxel sizes. do not hardcode any numbers from example.

tvol is my own tiny binary. all numbers little endian.

file starts with four ascii letters T V O L.

next four bytes version unsigned thirty two bit little endian.

next four bytes dtype code unsigned thirty two little endian. two means voxels are int16. sixteen means float32.

next twelve bytes three unsigned counts of voxels along each axis like width height depth historically nx ny nz.

next twelve bytes three float32 values saying mm per voxel per axis historically sx sy sz. they change every file anisotropic so read them from header.

next four bytes unsigned offset where voxel data starts.

after offset there are nx times ny times nz values in announced dtype. x runs fastest so index for x y z is x plus nx times open bracket y plus ny times z close bracket.

inside there is one solid bright mass. lens has point spread that makes edges fuzzy. interior flat bright. border dimmer because partly occupied and smeared to neighbours. background flat plus noise. some scans have one or two tiny bright specks far away trash keep biggest connected bright mass using twenty six neighbours.

threshold counting fails. blur conserves energy. so you need to think about background removal and how bright fully filled interior really is and how much total light belongs to main object plus halo. precise recovery needs most concentrated area not just bright voxel count. light is everywhere so find where concentration highest.

parse bytes yourself with only stdlib like struct. dont use numpy scipy skimage opencv pillow networkx igraph imageio pandas torch tensorflow or any array image graph library. dont use subprocess os system popen exec tricks or double underscore import importlib runpy ctypes eval exec compile shell.

at end print size mm3 as last word.
