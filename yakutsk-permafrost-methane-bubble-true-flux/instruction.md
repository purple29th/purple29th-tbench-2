I am Anya from Yakutsk in Sakha. My father works on permafrost methane. We drill 1m cores in Batagay crater and at 1am we image methane bubbles that glow with infrared dye, rig writes PMBF magic PMBF. Inside are elongated bubbles along ice veins that are real flux plus round water inclusion pores to ignore plus far dust specks from drill dust. Some cores have two distant bubble fields both count. I need true flux mg per m2 per day.

Please make file at /app/solve.py. We call python /app/solve.py path and last token is answer.

Example at /app/data/scene.pmbf about eight mg per m2 per day. Hidden uses random temp names like input_a3f9.pmbf with new sizes spacings gain blur.

File layout pmbf. My own tiny format little endian.

Four bytes ascii PMBF.
Four bytes uint32 version.
Four bytes uint32 dtype 2 int16 16 float32.
Twelve bytes three uint32 nx ny nz.
Twelve bytes three float32 sx sy sz mm per voxel.
Four bytes uint32 data offset where array starts can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty scales final flux sample one point zero hidden at ninety six one point two two ignore fails twenty two percent.
At offset you get nx times ny times nz samples X fastest.

Inside each cube elongated bubbles along ice veins count. Compact water pores round benign ignore. Tiny bright dots far away drill dust ignore. Twenty six neighbour connectivity.

Calibration flux equals volume mm3 times zero point seven two mg per m2 per day per mm3 times multiplier.

Naive levels fail, generous doubles, strict loses third.

Energy preserved. Total excess stays same. You must handle background bias median dimmest seventy percent, noise floor lower half MAD, far dust, interior level hidden by blur, avoid skirt as background, avoid jumping to specks, sum all elongated pieces.

Within percent possible three percent allowed.

Coding rules parse bytes yourself only stdlib struct sys math random tempfile re. No numpy scipy etc. No eval exec compile import chr ord bytes bytearray. No subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes nor hiding names. Do not open tests folder.

Print flux mg per m2 per day as last token.
