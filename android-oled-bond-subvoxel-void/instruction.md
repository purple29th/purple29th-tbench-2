my pixel factory qa line checks oled adhesive for trapped air voids using under display ir scanner mounted on android test rig. i dump raw backscatter cubes from vcsel diffuser + ir scatter sensor via android FileOutputStream. kotlin side writes ByteBuffer little endian into app private storage just like arcore depth dumps.

your job is script that turns one cube into physical air void volume cubic mm.

make file named solve dot py inside app folder. we will run like python app solve py /path/to/scan.obvl and we take last whitespace token printed as float volume. one sample you can try locally named scene dot obvl lives under app/data. hidden grading uses other dumps you never saw with different void sizes diffuser power voxel pitch spacing background ir dust specks. do not hardcode any numbers from sample size brightness.

obvl is tiny custom container i invented for oled bond scans. all ints and floats little endian.

first four bytes ascii O B V L magic.

next four bytes u32 version.

next four bytes u32 dtype code. two equals int16 scatter. sixteen equals float32 scatter.

next twelve bytes three u32 nx ny nz counts per axis width/height/depth. total voxels nx*ny*nz.

next twelve bytes three f32 sx sy sz mm per voxel per axis. anisotropic calibration from oled stack diffusion xy and bond thickness z. different per file so must read header every time do not assume.

next four bytes u32 data_offset where voxel payload starts.

after offset nx*ny*nz values of declared dtype. x is fastest: linear index for x y z = x + nx * (y + ny * z).

cube content: one main air void bubble plus occasional far dust speck blobs fibre reflections. vcsel diffuser plus oled stack gives anisotropic point spread wide laterally narrow axially because oled diffuses ir wide xy and bond thin so z narrow. so true shape: thick core where scatter bright and flat from air bubble, plus thin delam channels fingers along x y where voxel only partially filled so intensity lower. border voxels dimmer from partial fill and smear. flat ambient ir background plus faint per voxel noise. some scans have one or two extra tiny bright blobs far away dust artefacts trash keep main connected mass using 26 neighbours, pick by integrated mass not voxel count.

threshold counting cannot work: low cut includes huge blurred halo overestimates 70-120 percent. high cut misses thin partially filled delam channels underestimates 30-50 percent. no fixed cut works across files because diffuser power background pitch change per oled batch.

blur spreads energy but does not create or destroy photons. that physics makes precise subvoxel volume possible. best clue is where scatter most concentrated not just how many bright voxels. interior flat but hidden by blur noise. so true voxels = sum(background_subtracted intensity over void+halo) / plateau_amplitude. plateau is saturated interior where scatter most concentrated.

parse binary yourself using only stdlib like struct. banned: numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob any array image graph helper. banned runtime tricks: subprocess os.system os.popen exec double underscore import importlib runpy ctypes eval exec compile shell filesystem listing glob multiprocessing socket. also do not open / read tests directory.

at end print volume mm3 as last token. grading at 3 percent tolerance, exact thresholds not prescribed, you must find robust ones that work across scans with different power background pitch dust. 3 percent band allows some heuristic variation.
