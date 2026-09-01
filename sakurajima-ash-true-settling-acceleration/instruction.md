I am Haru from Sakurajima in Kagoshima. Sakurajima erupts almost every day and ash falls on my tea leaves. My grandfather says tea tastes worse when ash stays. At night we put sticky glass slides outside and tag ash with IR phosphor that shows settling motion as streaks. Humid air and lens smear the streaks but photons are conserved.

I need a small tool that tells me true settling acceleration in mm per second squared for all elongated ash streaks that are real fall. Some slides have two distant streaks far apart that both count.

Please make file at /app/solve.py. We call python /app/solve.py path and last token is answer.

Example at /app/data/scene.ashf inside container, about ten point two eight mm per second squared. Hidden uses different slides with new sizes spacings brightness diffusion pitch with random temp names like input_d9a3.ashf.

File layout ashf. My own tiny format, everything little endian.

Four bytes ascii ASHF.
Four bytes uint32 version.
Four bytes uint32 dtype code. Two means int16, sixteen means float32.
Four bytes uint32 width.
Four bytes uint32 height.
Four bytes float32 sx mm per pixel x.
Four bytes float32 sy mm per pixel y.
Four bytes uint32 data offset where array starts, can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty that scales final acceleration, changes per file, sample one point zero, hidden ninety six uses one point two two, ignore and you fail by twenty two percent.
At offset you get width times height samples, X fastest.

Inside each slide there is ash. Real is long ragged streaks along wind grain that count. There are also compact water droplets that are round and benign, do not count. Plus one to three tiny specks far away that are distant ash dust on window, ignore.

We use eight neighbour connectivity.

Calibration. Area equals count times sx times sy, length equals area divided by zero point three five mm, velocity equals length divided by zero point eight zero seconds, acceleration equals velocity divided by one point two zero seconds times multiplier equals area times two point nine seven six times multiplier mm per second squared. You first recover true area.

Naive levels fail. Generous includes aureole and almost doubles acceleration, strict loses tails and loses third to half.

Energy preserved.

You must handle background bias, noise floor, far specks, interior level, avoid skirt as background, avoid jumping to specks, sum all elongated pieces.

Within percent possible, three percent allowed.

Coding rules. Parse bytes yourself, only stdlib struct sys math random tempfile re. No numpy scipy skimage cv2 PIL etc. No eval exec compile import chr ord breakpoint bytes bytearray. No subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes nor hiding names. Do not open tests folder or mention test_outputs heldout reference. Work on any temp path.

Print acceleration in mm per second squared as last token.
