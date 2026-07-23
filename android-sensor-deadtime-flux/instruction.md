Our on-device particle counter logs how many events it detected in each short time bin, and saves them in a custom binary format we call flux. Write a Python script at /app/solve.py that reads one of these logs and prints the total true number of events over the whole recording.

Run it as:

    python3 /app/solve.py <path-to-log>

The log path is the first argument. Print the total as the final number on stdout. There is a sample log at /app/data/scene.flux to develop against, and we score your script on logs you have not seen.

How the counter behaves: whenever it records a count, it goes blind for a short dead time tau seconds. Any events that arrive while it is blind are missed, and being blind does not get extended by those missed events. So when events come in fast, the counter cannot keep up and the recorded counts are lower than the number of events that actually happened. Over a bin of width dt, if the true event rate is n per second, the recorded rate settles at n / (1 + n * tau). The header gives you dt and tau, and they are not the same in every log.

The flux format is ours, laid out little endian with a fixed header. The first four bytes are the magic FLUX. Then a uint32 version. Then a uint32 dtype code, where 2 means the per-bin counts are stored as uint16 and 4 means they are stored as uint32. Then a uint32 nbins giving the number of bins. Then a float32 dt, the bin width in seconds. Then a float32 tau, the dead time in seconds. Then a uint32 data_offset marking the byte where the counts begin. From there you get nbins recorded counts of the given dtype, one per bin, in order.

Parse the bytes yourself. You may not use numpy, scipy, or any other array, imaging, or graph library, and you may not shell out or import things dynamically (no subprocess, os.system, os.popen, __import__, importlib). Use only the Python standard library.

Print the total true number of events as the final number on stdout. We grade on logs you have not seen.
