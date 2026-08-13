I work on coastal tide gauges for a harbor dredging project. The moon M2 tide drives most water level swing but gauges also see S2 solar 12 hours O1 25.82 hours K1 23.93 hours plus slow linear drift from subsidence plus ship wakes that create tall isolated spikes and sensor noise.

Port authority needs true M2 amplitude in meters not raw wiggle size for dredge depth calibration. Simple RMS or peak to peak fails by 30 to 80 percent because record mixes several tides and occasional meter scale spikes.

You will write file at /app/solve.py . When graded we run python /app/solve.py path to file and take last printed token as meter amplitude.

We give one example at /app/data/scene.thld you can open. Hidden grading uses completely different gauges with random n dt gain drift constituent amplitudes phases noise spike positions and random temp file names. Do not hardcode numbers from example.

File format THLD Tidal Harmonic Level Data little endian:

Byte 0 to 3 ASCII magic THLD
Byte 4 to 7 uint32 version 1
Byte 8 to 11 uint32 dtype tag 2 means int16 scaled by 1000 16 means float32
Byte 12 to 15 uint32 n samples count 500 to 5000
Byte 16 to 19 float32 dt seconds sampling interval 300 to 900 seconds varies per file so you must read
Byte 20 to 23 float32 gain sensor calibration 0.85 to 1.35 observed heights equal true physical times gain You must divide by gain at end to report physical amplitude
Byte 24 to 27 float32 mean offset sea level offset varies but not needed
Byte 28 to 31 uint32 freq count number of harmonic constituents present 2 to 4 but you can assume at least M2 always present
Byte 32 to 35 uint32 data offset start of data block varied 48 64 80 96 112 128
Remaining to data offset is zero padding.

At data offset n samples float32 or int16 values depending on dtype of sea level height in meters times gain observed. Single dimension.

What is inside:
 Physical signal equals sum of Amp k times cos omega k times t plus phi k plus mean plus drift rate times t
 Frequencies rad per sec fixed physics:
  M2 2pi divided by 12.4206 times 3600 equals 0.0001405189
  S2 2pi divided by 12 times 3600 equals 0.000145444
  O1 2pi divided by 25.81934 times 3600 equals 0.0000675977
  K1 2pi divided by 23.93447 times 3600 equals 0.00007292115
 Amplitudes M2 0.6 to 2.8 m is scored others 0.15 to 0.8 m random phases.
 Drift rate about minus 0.00001 to plus 0.00001 m per sec linear.
 Gaussian noise sigma 0.04 to 0.12 m
 Spikes 2 to 8 isolated samples add plus 1.2 to plus 2.5 m or minus 1.2 to minus 2.5 m ship wakes far from tide must be rejected like dust specks but now time domain.

Why naive fails:
 max to min divided by 2 or RMS times sqrt2 absorbs S2 O1 K1 and drift and spikes and overestimates 30 to 60 percent. Spikes make it double.
 Counting only tallest peaks misses phase and still mixes other constituents.
 Ignoring sensor gain gives 15 to 35 percent systematic error because observed equals physical times gain.
 Grading signal is intact only for full separation of M2 from other tides handling of far outliers and correction for instrumental factors. Skipping any still fails above 3 percent.

We grade at 3 percent relative error. Simple methods are far outside that window.

Coding rules your solve.py is scanned:
 Parse bytes yourself. Only allowed imports struct sys math random tempfile re
 Forbidden numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath and any other array imaging graph lib plus subprocess importlib runpy ctypes
 Forbidden calls eval exec compile import chr
 Forbidden runtime subprocess os system os popen os exec os fork os walk os listdir os scandir os open pty any dir listing plus tricks hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray
 Do not try to open or list tests folder. Do not reference test outputs heldout reference volume gen GEOM TRUTH geometric truth in solver.
 Your solver must work on any random temp file path.

Print M2 physical amplitude in meters as last token for example 1.234 or 1.23e0
