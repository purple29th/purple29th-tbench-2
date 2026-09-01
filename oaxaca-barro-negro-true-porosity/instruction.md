I am Isabel from San Bartolo Coyotepec in Oaxaca Mexico, town of barro negro black clay pottery. My mother and I fire clay in underground pit kiln with mesquite wood at one am, smoke is black and hot. After firing we cut a sherd and do micro CT with iodine dye that glows in pores, rig writes BLCY magic BLCY with variable payload start and multiplier. Inside are firing cracks from wheel throwing that are elongated along forming grain that affect strength. Need true porosity percent for firing quality control.

I need a small tool that tells me total porosity percent summing all elongated firing cracks that are real pores. Some sherds have two distant crack fields both matter.

Please make file at /app/solve.py. We call python /app/solve.py path final token percent.

Example at /app/data/scene.blcy inside container about eight percent. Hidden uses totally different sherds with new sizes spacings brightness diffusion pitch random temp names like input_c4d1.blcy.

File layout blcy little endian.

Four bytes ascii BLCY.
Four bytes uint32 version.
Four bytes uint32 dtype two int16 sixteen float32.
Twelve bytes three uint32 nx ny nz.
Twelve bytes three float32 sx sy sz mm per voxel.
Four bytes uint32 data offset where array starts can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty scales final percent sample one point zero hidden at ninety six is one point two two ignore fails twenty two percent.
At offset you get nx times ny times nz samples X fastest.

Inside each cube elongated firing cracks along wheel grain count. Compact sand inclusions from clay that are round and benign do not count. Tiny bright dots far away kiln dust on window ignore.

We use twenty six neighbour connectivity.

Calibration porosity equals volume mm3 times zero point four eight percent per mm3 times multiplier. So you first recover true crack volume from smeared cloud then convert.

Naive levels fail. Generous includes halo and doubles porosity, strict loses tails and loses third.

Energy preserved total excess same. You must handle background bias median dimmest, noise floor MAD, far dust, interior level, avoid skirt as background, avoid jumping, sum all elongated.

Within percent possible three percent allowed.

Coding rules parse bytes yourself only stdlib struct sys math random tempfile re. No numpy scipy skimage cv2 PIL etc. No eval exec compile import chr ord breakpoint bytes bytearray. No subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes nor hiding names. Do not open tests folder.

Print porosity percent as last token.
