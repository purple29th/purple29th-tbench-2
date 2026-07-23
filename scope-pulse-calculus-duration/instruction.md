hey i am in particle lab reading photodiode pulses off oscilloscope after shaper amplifier. we flash and diode gives one clean square pulse that should be short but shaper smears it everywhere. looks like big fuzzy gaussian with tails. we need true original duration in ns not smeared length.

i need program that tells true physical pulse width before smear. precision matters for charge collection time.

make file named solve dot py inside app folder. we call it as python app solve py with dump path as argument. last word printed taken as duration.

you get one example to try named scene dot plse inside data folder that is inside app. hidden grading uses other dumps you never saw with different widths amplitudes sampling interval baseline noise and shaper sigma. do not hardcode numbers from example.

what is plse. our own small binary for pulse scope. everything little endian.

file starts with four ascii P L S E.

version is next four bytes unsigned thirty two little endian.

dtype code next four bytes unsigned thirty two little endian. two means int16 samples. sixteen means float32 samples.

next four bytes are unsigned counts of samples per trace historically n.

next four bytes are float32 sampling interval in ns per sample historically dt. changes every file so read it.

next eight bytes are two float32 values baseline scale? actually at 16 is float32 baseline offset? wait we store baseline at 16? let me recall we have data offset at 20 then baseline at 24 float32. so layout like this:

offset 0: magic PLSE
offset 4: version u32
offset 8: dtype u32 2=int16 16=float32
offset 12: n u32 num samples
offset 16: dt f32 ns per sample
offset 20: data_offset u32 where samples start
offset 24: baseline_hint f32? we write but you should ignore and estimate yourself robustly from data
offset 28-64 reserved.

after data_offset you have n values in announced dtype. x is time: index for t is t.

inside is one main pulse plus occasional far afterpulses tiny specks from reflections keep main connected mass using 1d neighbours contiguous.

center flat where photodiode saturated but hidden by shaper plus thin pre and post extensions low amplitude partial.

this is tricky and every agent will find it hard to be precise calculus needed. threshold counting never precise. low cutoff includes huge smeared tails overcounts eighty to one hundred thirty percent. high cutoff misses thin extensions that never get high enough undercounts thirty to fifty percent. no fixed cutoff works across files because amplitude baseline dt sigma change.

shaper spreads charge but does not create or destroy charge. that physics makes precise duration possible via calculus integral. total charge conserved so true width samples equals sum intensity minus baseline over pulse plus halo divided by plateau amplitude. duration ns equals width times dt.

simple tricks off large margin. grade at three percent tolerance only genuine precise method passes.

parse bytes yourself only stdlib like struct. do not use numpy scipy scikit image opencv pillow networkx igraph imageio pandas torch tensorflow or any array image graph helper. do not use subprocess os system popen exec double underscore import importlib runpy ctypes eval exec compile shell. do not open tests folder list filesystem.

print duration ns as last word.
