I am Bat from Khovsgol lake in northern Mongolia, we live in yurt made of sheep wool felt. In January it is minus thirty and wind cuts through felt if it is thin. At one am we image felt with thermal IR phosphor that glows where heat leaks through, rig writes YRFL magic YRFL with variable payload start and multiplier. Inside are heat leak channels that are elongated along felt pressing grain that are real leaks plus round lanolin blobs from sheep grease round to ignore plus far dust specks from steppe.

I need tool that tells true thermal conductivity W per mK.

Please make file at /app/solve.py call python /app/solve.py path last token W per mK.

Example at /app/data/scene.yrfl inside container about zero point zero three five W per mK. Hidden uses different felt pieces with new sizes spacings brightness diffusion pitch random temp names like input_e5f2.yrfl.

File layout yrfl little endian.

Four bytes ascii YRFL.
Four bytes uint32 version.
Four bytes uint32 dtype two int16 sixteen float32.
Twelve bytes three uint32 nx ny nz.
Twelve bytes three float32 sx sy sz mm per voxel.
Four bytes uint32 data offset where array starts can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty scales final W per mK sample one point zero hidden at ninety six is one point two two ignore fails twenty two percent.
At offset you get nx times ny times nz samples.

Inside each cube elongated heat channels along felt grain count. Compact lanolin blobs round benign ignore. Tiny far dust ignore.

Twenty six neighbour connectivity.

Calibration conductivity equals volume mm3 times zero point zero three five W per mK per mm3 times multiplier.

Naive fails doubles or loses third. Energy preserved.

You must handle background median dimmest seventy percent noise floor lower half MAD far dust interior level avoid skirt as background avoid jumping sum all elongated pieces.

Within three percent.

Coding rules only stdlib struct sys math random tempfile re. No numpy scipy etc.

Print W per mK as last token.
