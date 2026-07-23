my android warehouse app measures parcel volume using phone rear ToF LiDAR. i dump raw occupancy cubes from ARCore Depth API extended with Sensor.TYPE_TOF confidence. kotlin side writes ByteBuffer little endian via FileOutputStream into app private storage.

your job is script that turns one cube into physical parcel size cubic mm.

make file named solve dot py inside app folder. we will run like python app solve py /path/to/scan.tvol and we take last whitespace token printed as float volume. one sample you can try locally named scene dot tvol lives under app/data. hidden grading uses other dumps you never saw with different parcel dimensions emitter power voxel pitch spacing background IR multipath. do not hardcode any numbers from sample size brightness.

tvol is tiny custom container i invented for ToF cubes. all ints and floats little endian.

first four bytes ascii T V O L magic.

next four bytes u32 version.

next four bytes u32 dtype code. two equals int16 occupancy. sixteen equals float32 occupancy.

next twelve bytes three u32 nx ny nz counts per axis width/height/depth. total voxels nx*ny*nz.

next twelve bytes three f32 sx sy sz mm per voxel per axis. anisotropic calibration from camera intrinsics xy and ToF timing jitter z. different per file so must read header every time do not assume.

next four bytes u32 data_offset where voxel payload starts.

after offset nx*ny*nz values of declared dtype. x is fastest: linear index for x y z = x + nx * (y + ny * z).

cube content: one solid parcel plus occasional far flying-pixel specks from multipath. VCSEL IR emitter plus lens gives anisotropic point spread wide laterally narrow axially. so true shape: thick core where occupancy saturates to plateau amplitude from fully filled voxels, plus thin flaps straps tape fingers where voxel only partially filled so intensity never reaches plateau. border voxels dimmer both from partial occupancy and smear to neighbours. flat ambient IR background plus faint per-voxel read noise. some scans have one or two extra tiny bright blobs far away - depth flying pixels / multipath artefacts - must be dropped. keep only biggest connected bright mass using 26 neighbour connectivity (faces edges corners).

threshold and count cannot work: low cut includes huge blurred halo overestimates 80-130 percent. high cut misses thin partially filled flaps underestimates 30-50 percent. no fixed cut works across files because emitter power background and pitch change every file.

blur from normalized kernel conserves total IR energy, does not create or destroy. that makes precise sub-voxel volume possible if you separate main parcel from far specks, estimate ambient background without bias from parcel itself, figure true interior plateau where concentration highest, and integrate how much total background-subtracted light belongs to main object plus its faint halo deciding halo extent without bridging specks.

parse binary yourself using only stdlib like struct. banned: numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow any array image graph helper. banned runtime tricks: subprocess os.system os.popen exec double underscore import importlib runpy ctypes eval exec compile shell filesystem listing. also do not open / read tests directory.

at end print volume mm3 as last token.
