I work as a mixing engineer for a sampled piano library. Each note is a chord voiced with the tonic plus arrangement harmony major third f0 times 1.259921 equals 2 to power 4 divided by 12 perfect fifth f0 times 1.498307 equals 2 to power 7 divided by 12 octave 2 times f0 and the tonic bright second overtone 3 times f0 that adds air. During sampling the close mic picks up percussive keybed clicks tall isolated spikes that look like drum hits plus slow DC drift from phantom power heating sensor gain 0.85 to 1.35x and tape hiss noise.

Library needs true physical tonic fundamental amplitude in mix to balance arrangements automatically. If tonic weight wrong whole voicing sounds muddy or thin. Simple RMS or peak to peak fails 30 to 85 percent because chord mixes 5 tones and occasional click spikes make it double.

You will write file at /app/solve.py . When graded we run python /app/solve.py path to file and read last printed token as tonic amplitude in nominal volts.

We give one example at /app/data/scene.mthb you can open. Hidden grading uses completely different pianos with random n dt 0.25ms to 1ms f0 110 to 440Hz per file gain drift harmonic amplitudes phases noise spike positions and random temp file names. Do not hardcode numbers from example.

File format MTHB Music Tonic Harmonic Balance little endian:

Byte 0 to 3 ASCII magic MTHB
Byte 4 to 7 uint32 version 1
Byte 8 to 11 uint32 dtype tag 2 means int16 scaled times 1000 16 means float32
Byte 12 to 15 uint32 n samples 2000 to 6000
Byte 16 to 19 float32 dt seconds sampling interval 0.00025 to 0.001 seconds varies you must read
Byte 20 to 23 float32 f0 hz tonic fundamental frequency 110 to 440Hz varies per file you must read
Byte 24 to 27 float32 gain sensor calibration 0.85 to 1.35 observed equals true physical times gain You must divide at end.
Byte 28 to 31 float32 mean offset DC offset
Byte 32 to 35 uint32 freq count number of arrangement tones present 3 to 5 but tonic always present
Byte 36 to 39 uint32 data offset start of data block varied 48 64 80 96 112 128
Remaining to data offset zero padding.

At data offset n float32 or int16 values of observed waveform volts times gain.

Inside physical signal before gain equals sum Amp k times cos 2pi f k times t plus phi k plus mean plus drift rate times t
f k derived from f0:
 f0 equals tonic fundamental graded
 f third equals f0 times 1.259921049894873 major third equal temperament
 f fifth equals f0 times 1.498307076876682 perfect fifth
 f octave equals f0 times 2.0
 f harm2 equals f0 times 3.0 second overtone
Amplitudes tonic 0.6 to 2.8 V graded others 0.15 to 0.8 V random phases.
Drift rate minus 0.05 to plus 0.05 V per sec slow.
Noise sigma 0.04 to 0.12 V.
Spikes 2 to 8 isolated samples add plus 1.2 to plus 2.5 V or minus 1.2 to minus 2.5 V keybed clicks must be rejected similar to ship wakes but time domain audio clicks.

Why naive fails:
 RMS times sqrt2 or peak divided by 2 absorbs third fifth octave harm2 and drift and clicks and overestimates 30 to 60 percent. Clicks make it double.
 Single frequency fit without separating chord tones still 8 to 18 percent over on arrangement heavy configs.
 Ignoring sensor gain gives 15 to 35 percent systematic error because observed equals physical times gain.
 Grading signal requires separation of 5 arrangement tones from each other handling of far isolated clicks and correction for instrumental gain and drift. Skipping any still fails above 3 percent.

We grade at 3 percent relative error. Simple methods are far outside that window.

Coding rules your solve.py is scanned:
 Parse bytes yourself. Only allowed imports struct sys math random tempfile re
 Forbidden numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath and any other array imaging graph lib plus subprocess importlib runpy ctypes
 Forbidden calls eval exec compile import chr
 Forbidden runtime subprocess os system os popen os exec os fork os walk os listdir os scandir os open pty any dir listing plus tricks hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray
 Do not try to open or list tests folder. Do not reference test outputs heldout reference volume gen GEOM TRUTH geometric truth in solver.
 Your solver must work on any random temp file path.

Print tonic physical amplitude as last token for example 1.234 or 1.23e0
