hey so i am in pixel oled lab - we check display adhesive for trapped air voids. we have this android test rig with under-display ir scanner, vcsel diffuser + ir scatter sensor. kotlin side just does ByteBuffer little-endian and FileOutputStream into app private storage, same pattern as arcore depth dumps.

basically your job is a script that turns one cube into actual air void volume in cubic mm.

make file at `/app/solve.py`. we will run like `python3 /app/solve.py /path/to/scan.obvl` and we take last whitespace token as float volume. one sample you can try locally named `scene.obvl` lives under `/app/data`. hidden grading uses other dumps you never saw - different void sizes, diffuser power, voxel pitch, background ir, dust specks. dont hardcode any numbers from sample pls.

obvl is tiny custom container i invented for oled bond scans. all ints and floats little-endian.

- first four bytes ascii `OBVL` magic
- next four bytes u32 version, its 1
- next four bytes u32 dtype code, 2 means int16 scatter, 16 means float32 scatter
- next twelve bytes three u32 `nx ny nz` counts per axis width height depth, total voxels nx*ny*nz
- next twelve bytes three f32 `sx sy sz` mm per voxel per axis, anisotropic calibration from oled stack diffusion xy and bond thickness z. different per file so must read header every time, dont assume same
- next four bytes u32 `data_offset` where payload starts
- after offset nx*ny*nz values of that dtype, x is fastest so linear index for x y z = x + nx * (y + ny * z)

cube content: one main air void bubble plus occasional far dust speck blobs, fibre reflections that are not part of void. vcsel diffuser plus oled stack gives anisotropic point spread - wide laterally narrow axially becuase oled diffuses ir wide xy and bond thin so z narrow. so true shape is thick core where scatter bright flat from air bubble plus thin delam channels fingers along x y where voxel only partly filled so intensity lower. border voxels dimmer from partial fill and smear. flat ambient ir background plus faint per voxel noise. some scans have one or two extra tiny bright blobs far away dust artefacts trash you have to drop keep main connected mass using 26 neighbours, pick by integrated mass not just voxel count otherwise you pick dust.

threshold counting cannot work i tried. low cut includes huge blurred halo and overestimates 70-120 percent. high cut misses thin delam channels and underestimates 30-50 percent. no fixed cut works across files because diffuser power background pitch changes per oled batch.

blur spreads energy but does not create or destroy photons, that physics makes precise subvoxel possible. interior is flat but hidden by blur noise. best clue is where scatter most concentrated not just how many bright voxels. so true voxels = sum(background_subtracted intensity over void+halo) / plateau_amplitude, plateau is saturated interior where scatter most concentrated. you need to figure out how to estimate background, plateau, and halo integration robustly across scans.

parse binary yourself using only stdlib like struct, banned: numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os any array image graph helper. banned runtime tricks: subprocess os.system os.popen exec double underscore dunder except __name__/__main__ import importlib runpy ctypes eval exec compile shell filesystem listing glob multiprocessing socket pathlib Path shutil io.open getattr setattr hasattr globals locals vars dir chr ord base64 binascii codecs __builtins__ __dict__ __subclasses__ __mro__ etc. also do not open / read tests directory or heldout files or _gen.py - we check decoded string literals for obfuscated paths too.

at end print volume mm3 as last token, grading at 3 percent tolerance. exact thresholds not prescribed you must find robust ones that work across scans with different power background pitch dust. 3 percent band allows some heuristic variation but threshold shortcuts will fail.

this is factory oled qa precision escalation of android-depth-object-volume and android-tof-subvoxel-volume. those can be solved by threshold -> mask -> largest CC counting. here that pipeline is 70-120 percent wrong. conservation lands 0.2-1 percent here.
