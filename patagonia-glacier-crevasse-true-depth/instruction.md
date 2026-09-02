I am Martina from El Chalten in Patagonia Argentina. My brother is a mountain guide on Viedma glacier, biggest glacier in Argentina. Every December we drag ground penetrating radar on sled at one am because sun never sets, radar writes GLCR magic GLCR with variable payload start and multiplier. Inside radar volume are crevasses that are elongated along ice flow that cause falls. We need true depth in meters for rope planning.

I need a small tool that tells me total crevasse depth in meters summing all elongated crevasses that are real. Some volumes have two separate crevasses far apart both count, biggest only fails half.

Please make file at /app/solve.py. We call python /app/solve.py path and final token is answer meters.

Example at /app/data/scene.glcr inside container about two hundred eighty meters depth for scene with 1.15 factor and gain one. Hidden evaluation uses totally different volumes with new sizes spacings brightness diffusion pitch multiplier gain offset with random temp names like input_b7c2.glcr.

File layout glcr little endian with embed fix.

Four bytes ascii GLCR at zero.
Four bytes uint32 version at four.
Four bytes uint32 dtype code two int16 sixteen float32 at eight.
Twelve bytes three uint32 nx ny nz counts at twelve.
Twelve bytes three float32 sx sy sz mm per voxel at twenty four, this changes per file so you must read it, can be anisotropic e.g. 0.13 vs 0.09.
Four bytes uint32 data offset at thirty six where array starts, can be forty eight sixty four eighty ninety six one twenty eight must parse not hardcoded sixty four.
Four bytes float32 multiplier at forty that scales final meters sample one point zero hidden at ninety six uses one point two two ignore fails twenty two percent.
At data offset you get nx times ny times nz samples X fastest.

Inside each cube elongated crevasses along flow that count. Compact air bubbles round benign do not count. Tiny bright dots far away serac dust on radar window ignore. We use twenty six neighbour connectivity in three dimensions.

Calibration depth equals volume mm3 times one point one five meters per mm3 times multiplier. You first recover true crevasse volume from smeared cloud then convert to depth.

Naive brightness levels fail. Generous counts halo and doubles depth, strict loses thin tails loses third to half. Each file has different background gain scatter width no fixed level works.

Energy preserved. Total excess stays same. You must handle background from dimmest fraction, noise floor from lower half deviation, far dust to ignore, interior plateau brightness hidden by blur, avoid skirt as background, avoid jumping to specks, sum all elongated pieces.

Within percent possible, three percent allowed.

Coding rules parse bytes yourself only stdlib struct sys math random tempfile re. No numpy scipy skimage cv2 PIL etc. Do not open tests folder.

Print depth meters as last token.

Author Tosin Daniel Jimoh purple29th at meta.com
