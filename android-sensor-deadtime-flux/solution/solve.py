#!/usr/bin/env python3
"""Oracle: recover the total true number of events from a dead-time-limited
counter log, from scratch (standard library only).

The detector is non-paralyzable: after each recorded count it is blind for tau
seconds and events in that window are lost (they do not extend the window). Over
a bin of width dt, a true rate n is recorded as a measured rate m = n / (1 + n*tau),
so summing the raw counts undercounts the truth at high rates. Invert per bin:

    m = M / dt
    n = m / (1 - m*tau)
    true_count = n * dt = M / (1 - (M/dt)*tau)

then sum over bins. dt and tau are read from the header (they vary per file).
"""
import struct
import sys


def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:4] == b"FLUX", "bad magic"
    dtype = struct.unpack_from("<I", data, 8)[0]
    nbins = struct.unpack_from("<I", data, 12)[0]
    dt = struct.unpack_from("<f", data, 16)[0]
    tau = struct.unpack_from("<f", data, 20)[0]
    off = struct.unpack_from("<I", data, 24)[0]
    fmt = {2: "<%dH", 4: "<%dI"}[dtype] % nbins
    counts = list(struct.unpack_from(fmt, data, off))
    return counts, float(dt), float(tau)


def solve(path):
    counts, dt, tau = parse(path)
    total = 0.0
    for M in counts:
        m = M / dt
        denom = 1.0 - m * tau
        if denom <= 0:
            denom = 1e-9            # guard against the saturation pole
        total += M / denom
    return int(round(total))


if __name__ == "__main__":
    print(solve(sys.argv[1]) if len(sys.argv) > 1 else 0)
