I am Martina from El Chalten in Patagonia Argentina. My brother is a mountain guide on Viedma glacier, biggest glacier in Argentina. Every December we drag ground penetrating radar on sled at one am because sun never sets, radar writes GLCR magic GLCR with variable payload start and multiplier. Inside radar volume are crevasses that are elongated along ice flow that cause falls. We need true depth in meters for rope planning.

I need a small tool that tells me total crevasse depth in meters summing all elongated crevasses that are real. Some volumes have two separate crevasses far apart both count, biggest only fails half.

Please make file at /app/solve.py. We call python /app/solve.py path and final token is answer meters.

Example at /app/data/scene.glcr inside container about twelve meters depth. Hidden evaluation uses totally different volumes with new sizes spacings brightness diffusion pitch random temp names like input_b7c2.glcr.

File layout glcr little endian.

Four bytes ascii GLCR.
Four bytes uint32 version.
Four bytes uint32 dtype code two int16 sixteen float32.
Twelve bytes three uint32 nx ny nz counts.
Twelve bytes three float32 sx sy sz mm per voxel.
Four bytes uint32 data offset where array starts can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty scales final meters sample one point zero hidden at ninety six is one point two two ignore fails twenty two percent.
At offset you get nx times ny times nz samples X fastest.

Inside each cube elongated crevasses along flow that count. Compact air bubbles that are round and benign do not count. Tiny bright dots far away serac dust on radar window ignore.

We use twenty six neighbour connectivity in three dimensions.

Calibration depth equals volume mm3 times one point one five meters per mm3 times multiplier. So you first recover true crevasse volume from smeared cloud then convert to depth.

Naive brightness levels fail. Generous counts halo and doubles depth, strict loses thin tails loses third to half. Each file has different background gain scatter width no fixed level works.

Energy preserved. Total excess stays same. You must handle background bias median dimmest seventy percent, noise floor lower half median absolute deviation, far dust to ignore, interior level hidden by blur, avoid skirt as background, avoid jumping to specks, sum all elongated pieces.

Within percent possible, three percent allowed.

Coding rules parse bytes yourself only stdlib struct sys math random tempfile re. No numpy scipy skimage cv2 PIL etc. No eval exec compile import chr ord breakpoint bytes bytearray. No subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes nor hiding names. Do not open tests folder.

Print depth meters as last token.
