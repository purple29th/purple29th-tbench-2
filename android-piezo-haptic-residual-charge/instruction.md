I tune haptics for Android flagships that use piezo actuators under the display for crisp clicks. The piezo stack is driven high voltage and has dielectric absorption plus mechanical creep. After drive off there is residual current that drains from the stack and elastomer gasket. If we integrate wrong part, the click feels mushy and we get QA fails.

Write a program saved as /app/solve.py. It will be called as python /app/solve.py <trace_path> and must print true residual charge of main haptic pop in microcoulombs as its last token. Grading tolerance 3% relative. We have one sample trace at /app/data/scene.aphc for dev. Hidden evaluation uses different traces you never saw with different charge, drift, gain, RF period, total samples and baseline. Do not hardcode sample numbers. Must work on any file path given as first argument.

File format .aphc custom binary little endian:

- Bytes 0-3 ASCII magic APHC
- Bytes 4-7 uint32 version = 1
- Bytes 8-11 uint32 N = total int16 samples
- Bytes 12-15 uint32 data_offset = byte offset where current samples start
- Bytes 16-19 float32 sample interval in seconds (e.g. 0.0008), varies per file, must be read
- Bytes 20-23 float32 gain trim
- Bytes 24-27 uint32 baseline floor hint from firmware, do NOT trust, real baseline drifts with temperature and RF
- Header may have random padding from byte 28 up to data_offset. Use data_offset, do not assume 64. Hidden uses 32 40 48 64 80 96 128.
- At data_offset: N int16 little endian values, each is raw current in deci-mA. Convert to calibrated current in mA as raw_mA = value / 10.0 and calibrated_mA = raw_mA * gain_trim where gain_trim is float32 from header offset 20. You must multiply by gain_trim. Example if sample is 250 meaning 25.0 raw mA and gain_trim 1.2 then calibrated is 30.0 mA. Residual charge in microcoulombs for main pop is charge_uC = sum of calibrated_mA over main pop plus tails minus baseline times sample_interval_seconds times 1000.0. So final formula our grader uses is sum of value minus baseline divided by 10.0 times interval times gain times 1000 over main plus halo. If you ignore gain you will be low by gain factor and fail hidden where gain is not 1.0. Gain varies 0.85 to 1.35 per file and must be read. Sample file has gain 1.0 for local dev so you cannot see effect, hidden uses non unit gain. Do not ignore gain.

What is inside a trace? A drifting baseline that slowly rises plus RF sinusoidal ripple from display driver plus noise, one dominant haptic pop pulse that is flat-topped ideally but smeared by driver RC into broad peak with tails, a few isolated fast spikes far away from LRA cross-talk and finger tap, and two shallow wide humps: one from piezo dielectric creep and one from elastomer gasket relaxation. Each wide hump spans many samples but carries less total charge than main pop.

Why naive threshold fails: low threshold includes halo plus both creep humps plus RF crests and overcounts 65-95% over. High threshold cuts faint tail that still holds real charge and undercounts 30-50% under. Longest run by sample count picks a creep hump not main pop, because humps are longer yet weaker. No fixed level works across devices because gain, drift slope, RF amplitude/period and smear width shift per lot and per piezo bin.

The driver blur conserves charge: integral under smeared curve equals integral of ideal before blur. That lets you recover true charge despite smear, but you must be careful to get unbiased background without letting main pulse bias you, separate main pop from far spikes and dual creep humps, estimate true interior level without being fooled by spikes, and capture faint tail belonging to main until it fades into noise while not bridging to distant artifacts.

We grade at 3% relative. Threshold counting far outside.

Implementation rules: parse binary yourself, stdlib only. Allowed imports struct sys math random tempfile re collections. Forbidden and will make test_from_scratch fail: numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os pty importlib runpy ctypes and other array/imaging/graph libs. Forbidden calls eval exec compile __import__ chr ord breakpoint bytes bytearray. Forbidden runtime subprocess os.system os.popen os.exec os.fork os.walk os.listdir os.scandir os.open pty importlib runpy etc plus tricks hiding paths via chr bytes.fromhex base64 b64decode string concat building forbidden locations. Never open or list /tests, never mention test_outputs heldout reference_volume _gen GEOM_TRUTH geometric_truth inside solve.py. Work on random temp path, not hardcoded.

Print charge in microcoulombs as final token. Example 456.78
