I am Elena from Toconao on the edge of Salar de Atacama. My family are Lickanantay and we have scraped salt since my grandfather. Now the pools are for lithium. At one am we take glass slides to the crust and tag brine with fluorescein, lithium carbonate needles glow under four eight eight nm. The Atacama wind is cold and the salt dust gets everywhere. I have a small microscope with a sCMOS that writes a file I call BRIN.

I need a small tool that tells me total lithium mass in milligrams for all elongated brine needles that are real crystallization. The pools sometimes have two distant needle fields far apart that both matter, sum them, biggest only fails half.

Please make a file at /app/solve.py. We call it like python /app/solve.py path and final token is answer.

There is one example you can try at /app/data/scene.brin inside container, about one point zero nine mg. Hidden uses totally different slides with new sizes spacings brightness diffusion and pitch with random temp names like input_c7d2.brin.

File layout brin. My own tiny format, everything little endian.

Four bytes ascii BRIN.
Four bytes uint32 version.
Four bytes uint32 dtype code. Two means int16, sixteen means float32.
Four bytes uint32 width.
Four bytes uint32 height.
Four bytes float32 sx mm per pixel x.
Four bytes float32 sy mm per pixel y.
Four bytes uint32 data offset where array starts, can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty that scales final mg, changes per file, sample one point zero, hidden at ninety six is one point two two, ignore and you fail by twenty two percent.
At offset you get width times height samples, X fastest.

Inside each slide there is brine. Real is long needles along salt grain that count. There are also compact halite dust that is round and benign, do not count. Plus one to three tiny specks far away that are wind dust on window, ignore.

We use eight neighbour connectivity.

Calibration. Thickness assumed zero point one five mm, density two point one one mg per mm3, so mass mg equals area mm2 times zero point fifteen times two point one one times multiplier equals area times zero point three one six five times multiplier. You first recover true area from smeared cloud.

Naive levels fail. Generous counts fog and doubles mass, strict loses tails and loses third.

Energy preserved. Optics do not create photons, only move them. So sum of background removed glow over needle plus faint skirt divided by true core level gives true count.

You must handle background pulled by defect, noise floor per slide, far dust to ignore, interior level hidden by blur, avoid skirt as background, avoid jumping to specks, sum all elongated pieces.

Within percent possible, grading three percent.

Coding rules. Parse bytes yourself, only stdlib struct sys math random tempfile re. No numpy scipy skimage cv2 PIL etc. No eval exec compile import chr ord breakpoint bytes bytearray. No subprocess os system popen exec fork walk listdir scandir open pty importlib runpy ctypes nor hiding names with chr fromhex base64 b64decode. Do not open tests folder or mention test_outputs heldout _gen geometric_truth. Work on any random temp path.

Print mass in mg as last token.
