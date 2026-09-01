I am Bat from Khovsgol lake in northern Mongolia, we live in yurt made of sheep wool felt. In January it is minus thirty and wind cuts through felt if it is thin. At one am we image felt with thermal IR phosphor that glows where heat leaks through, rig writes YRFL magic YRFL with variable payload start and multiplier. Inside are heat leak channels that are elongated along felt pressing grain that are real leaks plus round lanolin blobs from sheep grease round to ignore plus far dust specks from steppe.

I need tool that tells true thermal conductivity W per mK for all elongated channels.

Please make file at /app/solve.py. We call python /app/solve.py path and last token is answer.

There is one example you can try at /app/data/scene.yrfl inside container, about eight point five W per mK for scene with 0.035 factor and gain one. Hidden evaluation uses totally different felt pieces I made with new sizes spacings brightness diffusion pitch multiplier gain offset with random temp file names like input_e5f2.yrfl. So you cannot hardcode.

File layout yrfl little endian with embed fix.

Four bytes ascii YRFL at zero.
Four bytes uint32 version at four.
Four bytes uint32 dtype code two means int16 sixteen means float32 at eight.
Twelve bytes three uint32 nx ny nz at twelve counts per axis.
Twelve bytes three float32 sx sy sz mm per voxel at twenty four, this changes per file so you must read it.
Four bytes uint32 data offset at thirty six where voxel array starts, can be forty eight sixty four eighty ninety six one twenty eight must parse not hardcoded sixty four.
Four bytes float32 multiplier at forty that scales final W per mK sample one point zero hidden at ninety six uses one point two two ignore and you fail by twenty two percent.
At data offset you get nx times ny times nz samples in dtype announced, X fastest.

Inside each cube elongated heat channels along felt grain that count. Compact lanolin blobs round benign ignore. Tiny far dust ignore.

We use twenty six neighbour connectivity in three dimensions.

Calibration conductivity equals volume mm3 times zero point zero three five W per mK per mm3 times multiplier.

I tried naive brightness levels and they are hopeless. If I am generous and count everything slightly above background my conductivity nearly doubles. If I am strict and only count very bright voxels I lose thin tails and lose third to half. Each file has different background gain and scatter width, no fixed level works.

Energy preserved. Total excess stays same, so threshold fails but conservation idea can work if you handle background bias that is pulled by defect, noise floor that varies per felt, far dust that must be ignored, interior level hidden by blur. You also must avoid counting skirt as background and avoid jumping to distant specks, sum all separate elongated pieces not just biggest.

If you get background and interior right you land within percent, grading allows three percent.

Coding rules. You must parse bytes yourself only stdlib struct sys math random tempfile re. You cannot use numpy scipy skimage cv2 PIL Pillow etc. Do not try to open or list tests folder. Your solver must work on any random temp path.

Print W per mK as last printed token.

Author Tosin Daniel Jimoh purple29th at meta.com
