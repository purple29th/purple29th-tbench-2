I am Jonas from Nida on Curonian Spit in Lithuania. After autumn storms the Baltic throws amber on sand and we walk at one am with UV lamp. Amber glows when tribo charged against sand, the glow is faint. I collect grains on black paper and photograph in a dark tent, my camera writes AMBR files.

I need a small tool that tells me total tribo charge in nano coulomb for all elongated amber veins that are real. Sometimes two distant veins on same paper both count, sum them.

Please make file at /app/solve.py. We call python /app/solve.py path and last token is answer.

Example at /app/data/scene.ambr inside container, about two point nine three nano coulomb. Hidden uses different papers with new sizes spacings brightness diffusion pitch with random names like input_b4e2.ambr.

File layout ambr. My own tiny format, everything little endian.

Four bytes ascii AMBR.
Four bytes uint32 version.
Four bytes uint32 dtype code. Two means int16, sixteen means float32.
Four bytes uint32 width.
Four bytes uint32 height.
Four bytes float32 sx mm per pixel x.
Four bytes float32 sy mm per pixel y.
Four bytes uint32 data offset where array starts, can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty that scales final charge, changes per file, sample one point zero, hidden at ninety six is one point two two, ignore and you fail by twenty two percent.
At offset you get width times height samples, X fastest.

Inside each paper there is amber. Real is long ragged veins along wood inclusion grain that count. There are also compact sand grain tribo dots that are round and benign, do not count. Plus one to three tiny specks far away that are Baltic sand dust on paper, ignore.

We use eight neighbour connectivity.

Calibration. Charge equals area mm2 times zero point eight five nano coulomb per mm2 times multiplier. You first recover true area.

Naive levels fail. Generous includes glow aureole and doubles charge, strict loses tails and loses third to half. No fixed level works.

Energy preserved. Optics do not create photons, only move them.

You must handle background, noise, far specks, interior level, avoid skirt as background and avoid jumping to specks, sum all elongated pieces.

Within percent possible, three percent allowed.

Coding rules. Parse bytes yourself, only stdlib struct sys math random tempfile re. No numpy scipy skimage cv2 PIL etc. No eval exec compile import chr ord breakpoint bytes bytearray. No subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes nor hiding names with chr fromhex base64 b64decode. Do not open tests folder or mention test_outputs heldout _gen. Work on any temp path.

Print charge in nano coulomb as last token.
