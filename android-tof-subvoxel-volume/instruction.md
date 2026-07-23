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

cube content: one solid parcel plus occasional far flying pixel specks from multipath. VCSEL IR emitter plus lens gives anisotropic point spread wide laterally narrow axially. so true shape: thick core where occupancy bright and flat, plus thin flaps straps tape fingers where voxel only partially filled so intensity lower. border voxels dimmer from partial fill and smear. flat ambient IR background plus faint per voxel noise. some scans have one or two extra tiny bright blobs far away depth artefacts trash keep main connected mass using 26 neighbours.

threshold counting cannot work: low cut includes huge blurred halo overestimates 80-130 percent. high cut misses thin partially filled flaps underestimates 30-50 percent. no fixed cut works across files because emitter power background pitch change.

blur spreads energy but does not create or destroy light. that physics makes precise subvoxel volume possible. best clue is where occupancy most concentrated not just how many bright voxels. interior flat but hidden by blur noise.

parse binary yourself using only stdlib like struct. banned: numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob any array image graph helper. banned runtime tricks: subprocess os.system os.popen exec double underscore import importlib runpy ctypes eval exec compile shell filesystem listing glob multiprocessing socket. also do not open / read tests directory.

at end print volume mm3 as last token. grading at 3 percent tolerance, exact thresholds not prescribed, you must find robust ones that work across scans with different power background pitch. 3 percent band allows some heuristic variation.
