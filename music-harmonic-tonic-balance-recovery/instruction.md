I work as a mixing engineer for a sampled piano library. Each note is a chord voiced with the tonic plus arrangement harmony: major third (f0 * 1.259921 = 2^(4/12)), perfect fifth (f0 * 1.498307 = 2^(7/12)), octave (2*f0), and the tonic's bright second overtone (3*f0) that adds air. During sampling, the close mic picks up percussive keybed clicks — tall isolated spikes that look like drum hits — plus a slow DC drift from phantom power heating, sensor gain 0.85-1.35x, and tape hiss noise.

The library needs the true physical tonic fundamental amplitude in the mix to balance arrangements automatically. If we get tonic weight wrong, the whole voicing sounds muddy or thin. Simple RMS or peak-to-peak fails 30-85% because the chord mixes 5 tones and occasional click spikes make it double.

You will write /app/solve.py . We run python /app/solve.py <path_to_file> and read last printed token as tonic amplitude in nominal volts.

We give one example at /app/data/scene.mthb you can open. Hidden grading uses completely different pianos with random n, dt (0.25ms to 1ms), f0 110-440Hz per file, gain, drift, harmonic amplitudes, phases, noise, spike positions and random temp file names. Do not hardcode numbers from example.

File format MTHB – Music Tonic Harmonic Balance – little endian:

Byte 0-3: ASCII magic MTHB
Byte 4-7: uint32 version=1
Byte 8-11: uint32 dtype tag 2=int16 scaled x1000, 16=float32
Byte 12-15: uint32 n_samples 2000-6000
Byte 16-19: float32 dt_seconds sampling interval 0.00025 to 0.001s – varies, you must read
Byte 20-23: float32 f0_hz tonic fundamental frequency 110-440Hz – varies per file, you must read
Byte 24-27: float32 gain sensor calibration 0.85-1.35 – observed = true_physical * gain . You must divide at end.
Byte 28-31: float32 mean_offset DC offset
Byte 32-35: uint32 freq_count number of arrangement tones present, 3-5, but tonic always present
Byte 36-39: uint32 data_offset start of data block varied 48 64 80 96 112 128
Remaining to data_offset zero padding.

At data_offset: n float32 or int16 values of observed waveform volts * gain.

Inside physical signal (before gain) = sum_k Amp_k * cos(2pi f_k t + phi_k) + mean + drift_rate*t
f_k derived from f0:
 f0 = tonic fundamental (graded)
 f_third = f0 * 1.259921049894873  (major third equal temperament)
 f_fifth = f0 * 1.498307076876682  (perfect fifth)
 f_octave = f0 * 2.0
 f_harm2 = f0 * 3.0  (second overtone)
Amplitudes: tonic 0.6-2.8 V graded, others 0.15-0.8 V, random phases.
Drift_rate -0.05 to +0.05 V/s slow.
Noise sigma 0.04-0.12 V.
Spikes: 2-8 isolated samples add +1.2 to +2.5 V or -1.2 to -2.5 V (keybed clicks), must be rejected – analogous to ship wakes in tide task but time-domain audio clicks.

Why naive fails:
- RMS*sqrt2 or max/2 absorbs third/fifth/octave/harm2 and drift → over 30-60%. Clicks make it double.
- Single frequency fit without separating chord tones still 8-18% over on arrangement-heavy configs.
- Gain ignored → 15-35% error.

What works (same robust core as tide task but music arrangement):
- Median and MAD for noise sigma, flag spikes >5.5 sigma from median.
- Linear detrend on inliers via least squares to remove DC+drift.
- Multi-frequency LS: build A with columns [cos(2pi f_k t), sin(2pi f_k t)] for each arrangement frequency (k = tonic, third, fifth, octave, harm2). Solve normal equations AtA x = Atb via Gaussian elimination from scratch. Tonic amplitude = hypot(C_tonic, S_tonic)/gain.
- Second pass spike rejection after detrending at 5 sigma.

We grade 3% relative.

Coding rules – your solve.py scanned:
- Parse bytes yourself. Only allowed imports: struct sys math random tempfile re
- Forbidden: numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath etc plus subprocess importlib runpy ctypes
- Forbidden calls: eval exec compile __import__ chr ord breakpoint bytes bytearray
- Forbidden runtime: subprocess os.system os.popen os.exec os.fork os.walk os.listdir os.scandir os.open pty any dir listing, hiding paths via chr bytes fromhex base64 b64decode bytearray tricks
- Do not open or list tests folder. Do not reference test_outputs heldout reference_volume _gen GEOM_TRUTH geometric_truth in solver.
- Must work on any random temp file path.

Print tonic physical amplitude as last token, e.g. 1.234 or 1.23e-0
