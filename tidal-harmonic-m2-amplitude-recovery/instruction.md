I work on coastal tide gauges for a harbor dredging project. The moon's M2 tide (principal lunar semidiurnal, period 12.4206 hours) drives most of the water level swing, but our gauges also see S2 (solar 12h), O1 (25.82h), K1 (23.93h), a slow linear drift from subsidence, plus ship wakes that slam the pier and create tall isolated spikes, and sensor noise.

The port authority needs the true M2 amplitude in meters, not the raw wiggle size, to calibrate dredge depth. Simple RMS or peak-to-peak fails by 30-80% because the record mixes several tides and occasional meter-scale spikes.

You will write /app/solve.py . We run python /app/solve.py <path_to_file> and take the last printed token as meter amplitude.

We give you one example at /app/data/scene.thld you can open. Hidden grading uses completely different gauges with random n, dt, gain, drift, constituent amplitudes, phases, noise, spike positions and random temp file names. Do not hardcode numbers from the example.

File format THLD – Tidal Harmonic Level Data – little endian:

Byte 0-3: ASCII magic THLD
Byte 4-7: uint32 version =1
Byte 8-11: uint32 dtype tag 2=int16 scaled by 1000, 16=float32
Byte 12-15: uint32 n_samples – number of samples, 500 to 5000
Byte 16-19: float32 dt_seconds – sampling interval, 300 to 900 seconds, varies per file so you must read
Byte 20-23: float32 gain – sensor calibration 0.85 to 1.35 – observed heights = true_physical * gain . You must divide by gain at end to report physical amplitude.
Byte 24-27: float32 mean_offset – mean sea level offset, varies but not needed
Byte 28-31: uint32 freq_count – number of harmonic constituents present, 2 to 4, but you can assume at least M2 always present
Byte 32-35: uint32 data_offset – start of data block, varied 48 64 80 96 112 128
Remaining to data_offset is zero padding.

At data_offset: n_samples float32 or int16 values (depending on dtype) of sea level height in meters * gain (observed). x fastest trivial 1D.

What is inside:
- Physical signal = sum_k Amp_k * cos(omega_k * t + phi_k) + mean + drift_rate * t
  Frequencies (rad/s) fixed physics:
  M2: 2pi/(12.4206*3600) = 0.0001405189...
  S2: 2pi/(12*3600)=0.000145444...
  O1: 2pi/(25.81934*3600)=0.0000675977...
  K1: 2pi/(23.93447*3600)=0.00007292115...
  Amplitudes: M2 0.6-2.8 m is scored, others 0.15-0.8 m, random phases.
- Drift_rate ~ -0.00001 to +0.00001 m/s ( -0.86 to +0.86 m/day) linear.
- Gaussian noise sigma 0.04-0.12 m
- Spikes: 2-8 isolated samples add +1.2 to +2.5 m or -1.2 to -2.5 m (ship wakes) far from tide, must be rejected, like dust specks in earlier tasks but now time domain.

Why naive fails:
- max-min /2 or RMS*sqrt2 absorbs S2 O1 K1 and drift and spikes → overestimates 30-80%. In spike_heavy configs and arrangement-heavy configs the naive error exceeds our 3% budget by large margins.
- Counting only tallest peaks misses phase and still mixes other constituents.
- Ignoring sensor gain gives 15-35% systematic error because observed = physical * gain.
- The grading signal is intact only for a full separation of M2 from other tides, handling of far outliers, and correction for instrumental factors. Skipping any of those still fails >3%.

We grade at 3% relative error. Simple methods are far outside that window.

Coding rules – your solve.py is scanned:
- Parse bytes yourself. Only allowed imports: struct sys math random tempfile re
- Forbidden: numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath and any other array/imaging/graph lib, plus subprocess importlib runpy ctypes
- Forbidden calls: eval exec compile __import__ chr
- Forbidden runtime: subprocess os.system os.popen os.exec os.fork os.walk os.listdir os.scandir os.open pty any dir listing, plus tricks hiding forbidden file names with chr bytes fromhex base64 b64decode bytearray
- Do not try to open or list tests folder. Do not reference test_outputs heldout reference_volume _gen GEOM_TRUTH geometric_truth in solver.
- Your solver must work on any random temp file path.

Print M2 physical amplitude in meters as last token, e.g. 1.234 or 1.23e-0
