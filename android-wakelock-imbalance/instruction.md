my android power lab app measures wakelock leak after Doze using phone power manager. i dump raw wakelock events from PowerManager WKLK trace extended with thread id. kotlin side writes ByteBuffer little endian via FileOutputStream into app private storage.

your job is script that turns one trace into total leaked hold time ms.

make file named solve dot py inside app folder. we will run like python app solve py /path/to/scan.wklk and we take last whitespace token printed as int leaked ms. one sample you can try locally named scene dot wklk lives under app/data. hidden grading uses other dumps you never saw with different id counts thread counts event counts offsets timing patterns leak totals tens to hundreds of millions ms. do not hardcode any numbers from sample size leak.

wklk is tiny custom container i invented for wakelock traces. all ints little endian.

first four bytes ascii W K L K magic.

next four bytes u32 version value 1.

next four bytes u32 event count N.

next four bytes u32 data_offset where event array starts.

next bytes from 16 to data_offset minus 1 is padding that may be garbage bytes, ignore. may contain fake WKLK magic and random bytes.

after offset N events each 16 bytes: int32 id signed system wakelocks use negative range, u32 type 1 acquire 0 release for positive ids inverted for negative, u32 timestamp ms, u32 thread id. for type 2 timeout acquire? actually v0.19 has type up to 1 only plus negative inverted. but spec says 0 release 1 acquire.

Struct format <iIII little endian per event, but header is <4sIII plus padding. you must respect data offset, do not hardcode header size. heldouts use varied offsets 16,20,24,32,40,64,96,128,192,256.

trace content: many wakelock ids observed across many threads plus occasional far system force clears from Doze. each trace has up to 2500 ids 30 percent negative, up to 24 threads including system thread 0, up to 50000 events. same id can be held by several threads at same time each (id, thread) is independent hold counted separately. several threads may hold same id at once. every hold still active at end is counted. dump contains messy real patterns from concurrent logger: duplicate acquire logs while already held, dangling releases with no matching hold, cross thread release attempts from binder calls that do not actually release another thread holder, reacquire after balanced cycles, and system force releases that clear holders.

threshold counting cannot work: per-id counting ignoring thread undercounts 60 to 70 percent because several threads can hold same id and each leak must be summed, and also overcounts 60 to 92 percent when cross thread noise mistaken as balancing true holder. file order instead of timestamp overcounts 30 to 55 percent and undercounts 20 to 40 percent randomly. global trace end instead of per-pair last observation overcounts 42 to 73 percent. first ever acquire instead of final interval start overcounts 120 to 310 percent. duplicate acquire idempotency ignored overcounts 20 to 45 percent. thread 0 global force release ignored overcounts 25 to 45 percent. unsigned parsing of signed ids misgroups 20 percent. hardcoding data offset 64 fails 6 of 8 heldouts. no fixed shortcut passes exact match.

even ids are ref-counted multiple acquires stack need equal releases, odd ids are binary idempotent holding stays 1 not incremented. system wakelocks negative have inverted type 0 means acquire 1 means release opposite of positive. even odd rule based on abs value. thread 0 release for given id releases all holders of that id across all threads regardless of refcount. release id 0 from thread 0 is full system suspend clears all ids.

blur spreads? actually hold age is pair own timeline not global. that physics makes precise leak possible. best clue is where pair last seen not global max. interior flat? actually earlier balanced cycles irrelevant. if pair final leak is just single acquire line with no later activity for that pair its leaked age is zero. duplicate while held updates last observation but does not restart interval for odd binary, for even increments count. per-pair last observation not global trace end.

parse binary yourself using only stdlib like struct sys. banned: numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os posixpath ntpath genericpath importlib runpy ctypes pty base64 binascii codecs builtins zlib. banned runtime tricks: eval exec compile __import__ getattr setattr hasattr globals locals vars dir chr ord breakpoint. also do not open / read tests directory. we enforce via AST import and os-attribute checks plus path-like literal scan.

at end print total leaked ms as last token. grading exact integer match, no tolerance, exact thresholds not prescribed, you must find robust handling that works across scans with different id counts thread counts timing patterns. exact match needed for battery blame.

implementation notes: trace may have up to 50000 events, same timestamp collisions 50 percent, cross-thread 10-16 per acquire. O n log n sort needed, use iterative. recursive will hit recursion limit? actually iterative stack needed for holds.

this task is about wakelock imbalance power manager leak, not about fingerprint oil smear, not about tof subvoxel volume, not about bitmap pool leak.

good luck.
