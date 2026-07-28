hey so i am in android display lab we check mura ink pooling after lamination. we have this test rig with under display rgb sensor that shines and captures luminance. kotlin side dumps ByteBuffer little endian via FileOutputStream into app storage same as arcore depth.

basically your job is script that turns one 2d luminance map into true ink pool area in square mm.

make file at `/app/solve.py`. we will run like `python3 /app/solve.py /path/to/scan.dmip` and we take last whitespace token as float area. one sample you can try locally named `scene.dmip` lives under `/app/data`. hidden grading uses other dumps you never saw with different pool sizes, backlight power, pixel pitch, background luminance, dust specks. dont hardcode numbers from sample pls.

dmip is tiny custom container i invented for display mura ink pool maps. all ints floats little endian.

- first four bytes ascii `DMIP` magic
- next four bytes u32 version its 1
- next four bytes u32 dtype code 2 means int16 luminance 16 means float32 luminance
- next eight bytes two u32 `nx ny` counts per axis width height total pixels nx*ny
- next eight bytes two f32 `sx sy` mm per pixel per axis anisotropic calibration from display lamination stretch xy. different per file so must read header every time dont assume same
- next four bytes u32 data_offset where payload starts
- after offset nx*ny values of that dtype x is fastest so linear index for x y = x + nx*y

image content: one main ink pool blob plus occasional far dust specks fibre reflections not part of pool. rgb sensor plus diffuser gives wide point spread in xy because adhesive diffuses. so true shape is thick core where ink pooling bright flat plus thin bleed fingers along x y where pixel only partly filled so intensity lower. border pixels dimmer from partial fill and smear. flat ambient backlight background plus faint per pixel noise. some scans have one or two extra tiny bright blobs far away dust artefacts trash you have to drop keep main connected mass using 8 neighbours pick by integrated mass not just pixel count otherwise you pick dust.

threshold counting cannot work i tried. low cut includes huge halo overestimates 60 to 110 percent. high cut misses thin bleed fingers underestimates 25 to 45 percent. no fixed cut works across files because backlight power background pitch changes per batch.

blur spreads light but does not create or destroy photons. interior flat but hidden by blur noise. best clue is where luminance most concentrated not just how many bright pixels. so true area = sum(background subtracted intensity over pool+halo) / plateau_amplitude * sx*sy.

parse binary yourself using only stdlib like struct. banned: numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os any array image graph helper. banned runtime tricks: subprocess os.system os.popen exec double underscore dunder except __name__/__main__ import importlib runpy ctypes eval exec compile shell filesystem listing glob multiprocessing socket pathlib Path shutil io.open getattr setattr hasattr globals locals vars dir chr ord base64 binascii codecs __builtins__ __dict__ __subclasses__ __mro__ etc. also do not open / read tests directory or heldout files.

at end print area mm2 as last token, grading at 3 percent tolerance. exact thresholds not prescribed you must find robust ones that work across scans with different power background pitch dust. 3 percent band allows some heuristic variation but threshold shortcuts will fail.

this is display mura ink pool version of oled bond void. oled bond void uses mm3 volume, here we use mm2 area in 2d. same conservation physics but 2d and different pitch and file magic. threshold counting fails similarly.

good luck, this one is subtle becuase bleed fingers are thin and dust far.
