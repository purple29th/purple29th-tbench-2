I am capturing a grand piano for a film scoring sample set. Each sample stacks a tonic pitch with arranged voices that fill the staff. The voiced set uses equal temperament major third at ratio 1.259921 fifth at 1.498307 octave at 2 second overtone at 3. These extra voices create harmonic richness but they also hide the tonic level that we need for auto balancing across velocity layers.

The recorded waveform includes tape hiss plus slow voltage drift from phantom heating plus sudden keybed clicks which appear as isolated tall transients that look like percussion hits. The mic preamp adds a gain factor between 0.85 to 1.35 that scales everything. The library engine needs true physical tonic fundamental amplitude after gain correction otherwise mixes sound muddy.

You will create a solver file at /app/solve.py . During grading we execute python /app/solve.py path to audio file and we read final printed token as the tonic level in volts.

For local development you have a sample file at /app/data/scene.mthb that you may inspect inside the container. Hidden evaluation uses completely different pianos different sample counts different sampling intervals different tonic pitches between 110 and 440 hertz different gains different drifts different overtone amplitudes phases noise levels click positions and random temp names. Hardcoding numbers from the sample will fail.

File container MTHB Music Tonic Harmonic Balance is little endian:

Byte 0 to 3 ASCII tag MTHB
Byte 4 to 7 unsigned int version 1
Byte 8 to 11 unsigned int dtype tag 2 means int16 scaled by 1000 16 means float32
Byte 12 to 15 unsigned int n samples between 2000 and 6000
Byte 16 to 19 float32 dt seconds sample period 0.00025 to 0.001 varies per file you must read
Byte 20 to 23 float32 f0 hertz tonic base frequency 110 to 440 varies you must read
Byte 24 to 27 float32 gain mic pre gain 0.85 to 1.35 observed equals true times gain you must undo at end
Byte 28 to 31 float32 mean offset DC level
Byte 32 to 35 unsigned int freq count arrangement voices present 3 to 5 but tonic always present
Byte 36 to 39 unsigned int data offset start of waveform varied among 48 64 80 96 112 128 zeros padded otherwise
At data offset n values float32 or int16 holding observed volts times gain.

Signal model before gain equals sum over arrangement voices Amp k times cos 2 pi f k t plus phi k plus mean plus drift rate times t
Frequencies from f0:
 tonic f0 graded value we score
 third f0 times 1.259921049894873 equal tempered major third
 fifth f0 times 1.498307076876682 perfect fifth
 octave f0 times 2
 overtone f0 times 3
Amplitudes tonic 0.6 to 2.8 volts scored others 0.15 to 0.8 volts random phases.
Drift rate about minus 0.05 to plus 0.05 volts per sec.
Noise sigma 0.04 to 0.12 volts hiss.
Clicks 2 to 8 positions each adds plus 1.2 to plus 2.5 or minus 1.2 to minus 2.5 volts isolated.

Why simple level fails:
 Simple root mean square times root two or peak over two lumps together third fifth octave overtone and drift and clicks and gives 30 to 85 percent too high.
 Single tone projection without separating other chord voices still 8 to 18 percent high on dense voicings.
 Forgetting gain leaves 15 to 35 percent bias because more gain looks like more level but is just scaling.
 To stay inside 3 percent you must handle isolated clicks tolerate drift and disentangle the five voicings while undoing gain. Skipping any part still fails the budget.

We check 3 percent relative.

Implementation notes your solve.py gets scanned:
 Read bytes yourself. Only allowed modules struct sys math random tempfile re
 Blocked numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath and any array imaging graph package plus subprocess importlib runpy ctypes
 Blocked calls eval exec compile import chr
 Blocked runtime subprocess os system os popen os exec os fork os walk os listdir os scandir os open pty any directory listing plus hiding tricks with chr bytes fromhex base64 b64decode bytearray
 Do not open or list tests directory. Do not mention test outputs heldout reference volume gen GEOM TRUTH geometric truth inside solve.
 Your code must work on any random temp path not a fixed one.

Output tonic physical amplitude volts as last token for instance 1.234
