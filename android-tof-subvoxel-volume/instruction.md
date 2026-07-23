Write a Python script at /app/solve.py that takes the path to a scan file as its first argument and prints the volume as the final number on stdout

You can test it using the sample scan at /app/data/scene.tvol and we will score your script on scans you have not seen so it needs to work in general

Run it as python3 /app/solve.py <path to scan>

We have a time of flight depth camera that saves a small 3D scan in our own format called tvol and your job is to read one of these scans and print how big the scanned object is in cubic millimetres

A tvol file uses little endian bytes and starts with the text TVOL in the first four bytes then at byte four there is a version stored as a uint32 and at byte eight there is a data type code stored as a uint32 where 2 means the voxel values are int16 and 16 means the voxel values are float32 and at byte twelve there are three uint32 values nx ny and nz for the dimensions and at byte twenty four there are three float32 values sx sy and sz for the voxel size in millimetres along x y and z and at byte thirty six there is a uint32 called data offset that tells you where the voxel values begin

After the data offset there are nx times ny times nz values of the given type stored with x changing fastest then y then z so the voxel at x y z is at index x plus nx times open parenthesis y plus ny times z close parenthesis

In the scan the object appears as a bright region with soft edges and each voxel value indicates how much of that voxel is filled by the object so voxels fully inside the object have a high peak value while partially covered voxels read lower and the optics blur readings into nearby voxels and there is also a flat background level plus noise and sometimes a few isolated bright dots away from the main object and voxel sizes differ across axes and across scans so always read sx sy and sz from the header

Parse the bytes yourself using only the Python standard library and do not use numpy scipy scikit image opencv pillow networkx igraph or any other array imaging or graph library and do not shell out or import things dynamically so no subprocess os system os popen dunder import or importlib

Print the object volume in cubic millimetres as the last number on stdout and we test your script on scans you have not seen
