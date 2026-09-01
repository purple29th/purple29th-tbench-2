I am Linh from Ca Mau at the tip of Mekong delta. My father farms mudskippers in mangrove burrows. The burrows go sideways under prop roots and baby fish hide there when tide is low. At night we push a thin slice of mud into a chamber with oxygen phosphor that glows where oxygen leaks from burrow walls. The mud turbidity smears the glow, looks bigger than true channel.

I need a small tool that tells me total oxygen flux in microliter per minute for all elongated burrow channels that are real breathing. Some slices have two separate channels far apart that both breathe, you must sum.

Please make file at /app/solve.py. We call python /app/solve.py path and last token is answer.

Example slice at /app/data/scene.burw inside container, about one point five five microliter per minute. Hidden evaluation uses totally different slices with new sizes spacings brightness diffusion pitch with random temp names like input_f2a1.burw.

File layout burw. My own tiny format, everything little endian.

Four bytes ascii BURW.
Four bytes uint32 version.
Four bytes uint32 dtype code. Two means int16, sixteen means float32.
Four bytes uint32 width.
Four bytes uint32 height.
Four bytes float32 sx mm per voxel x.
Four bytes float32 sy mm per voxel y.
Four bytes uint32 data offset where array starts, can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty that scales final flux, changes per file, sample one point zero, hidden ninety six uses one point two two, ignore and you fail by twenty two percent.
At offset you get width times height samples, X fastest.

Inside each slice there is burrow. Real is long ragged channels along root grain that count. There are also compact crab pellet blobs that are round and benign, do not count. Plus one to three tiny specks far away that are mud dust on chamber, ignore.

We use eight neighbour connectivity.

Calibration. Flux equals area mm2 times zero point four five microliter per minute per mm2 times multiplier. You first recover true area from smeared cloud.

Naive levels fail. Generous includes aureole and doubles flux, strict loses tails and loses third to half. No fixed level works because background and blur vary.

Energy preserved. Total excess stays same.

You must handle background bias, noise floor, far specks, interior level, avoid skirt as background, avoid jumping to specks, sum all elongated pieces.

Within percent possible, three percent allowed.

Coding rules. Parse bytes yourself, only stdlib struct sys math random tempfile re. No numpy scipy etc. No eval exec compile import chr ord breakpoint bytes bytearray. No subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes nor hiding names. Do not open tests folder or mention test_outputs heldout reference. Work on any temp path.

Print flux in microliter per minute as last token.
