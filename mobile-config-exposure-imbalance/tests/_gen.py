#!/usr/bin/env python3
"""Deterministic generator for mobile-config-exposure-imbalance .mcfg scans.

DEV/reproducibility tool, co-located with the tests so it is NOT shipped into
the agent container. Regenerates the sample + held-out files byte-for-byte.

Each held-out STACKS many independent traps at once (all within the instruction's
stated contract), so a trial has to get every one right to pass:

  * true answer   : reachable mutual-dependency island (SCC) with the largest
                    total weight (root value excluded) meeting the threshold
  * unreachable   : an SCC with a LARGER total that is NOT reachable from root 0
  * count trap    : a reachable SCC with MORE nodes but a smaller total
  * root-in-cycle : root 0 sits in a cycle with a huge value; excluding it is
                    required, and its with-root total would otherwise win
  * singleton     : the biggest reachable island is a single node (no cycle)
  * boundary      : an island exactly AT threshold counts; one just under does not
  * negatives     : signed values inside an island
  * dangling deps : dependency ids that point to non-existent nodes (ignore)
  * self/dup edges: self-loops and duplicate edges
  * scale/deep    : a ~2000-node file with a long chain (recursion dies) and
                    enough edges that pairwise mutual-reachability times out

Format (little-endian): magic 'MCFG', uint32 version, uint32 node_count,
uint32 data_offset, uint32 weight_threshold, header padded to data_offset. Then
per node: int32 id, int32 value, uint32 dep_count, dep_count * uint32 dep_id.

Run:  python3 _gen.py <output_dir>
"""
import os
import struct
import sys

MAGIC = b"MCFG"
DANGLING = 4_000_000_000  # valid uint32, no such node


def _lcg(seed):
    s = seed & 0xFFFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s


class Builder:
    def __init__(self, threshold, offset=64):
        self.threshold = threshold
        self.offset = offset
        self.nodes = []          # (id, value, [deps])
        self._ids = set()

    def add(self, nid, value, deps):
        assert nid not in self._ids, f"dup id {nid}"
        self._ids.add(nid)
        self.nodes.append((nid, value, list(deps)))

    def cycle(self, ids, values, extra_deps=None):
        """Add a directed cycle over ids (a single SCC)."""
        for i, nid in enumerate(ids):
            deps = [ids[(i + 1) % len(ids)]]
            if extra_deps and nid in extra_deps:
                deps += extra_deps[nid]
            self.add(nid, values[i], deps)

    def pack(self):
        hdr = bytearray(self.offset)
        hdr[0:4] = MAGIC
        struct.pack_into("<I", hdr, 4, 1)
        struct.pack_into("<I", hdr, 8, len(self.nodes))
        struct.pack_into("<I", hdr, 12, self.offset)
        struct.pack_into("<I", hdr, 16, self.threshold)
        body = bytearray()
        for nid, val, deps in self.nodes:
            body += struct.pack("<iiI", nid, val, len(deps))
            for c in deps:
                body += struct.pack("<I", c & 0xFFFFFFFF)
        return bytes(hdr) + bytes(body)


# --------------------------------------------------------------------- scene ---

def build_scene():
    b = Builder(threshold=0, offset=64)
    # root in a small cycle (its value excluded); a bigger reachable 2-cycle wins
    b.add(0, 100, [1, 4])
    b.cycle([1, 2, 3], [80, 90, 50])   # reachable SCC total 220
    b.cycle([4, 5], [30, 20])          # reachable SCC total 50
    return b


# ---------------------------------------------------------------- held-outs ---

def build_heldout_1():
    """threshold 0, offset 64. Answer is a 3-cycle (2500) that beats a large
    reachable singleton (2000) and a 5-node count-trap cycle (2400). A larger
    4-cycle (9000) is unreachable. Root sits in a cycle."""
    b = Builder(threshold=0, offset=64)
    # root in a cycle with huge value -> must exclude root
    b.cycle([0, 900, 901], [50000, 40, 50])   # excl-root total 90
    # root fans out to the reachable structures
    b.nodes[0] = (0, 50000, [900, 10, 20, 30, 700, DANGLING, 0])  # dangling + self-loop
    # decoy 3-cycle total 2500 (traps "cycles only" thinking: it is NOT the answer)
    b.cycle([10, 11, 12], [900, 800, 800])
    # count trap: reachable 5-cycle total 2400 (more nodes, less weight)
    b.cycle([20, 21, 22, 23, 24], [480, 480, 480, 480, 480])
    # TRUE ANSWER: a reachable singleton (no cycle) total 2600 -> island of size 1
    b.add(30, 2600, [31])
    b.add(31, 100, [])                # small reachable singleton
    # unreachable 4-cycle total 9000 (larger but not reachable from 0)
    b.cycle([40, 41, 42, 43], [2250, 2250, 2250, 2250])
    # reachable singleton with dangling + duplicate edges
    b.add(700, 300, [10, 10, DANGLING])
    return b


def build_heldout_2():
    """threshold 610, offset 96. The winning island totals EXACTLY 610, so a
    strict > comparison (instead of >=) drops it to 0. A 600 island is just
    under. An island with a negative member. Root in a cycle. A larger
    unreachable island (20000) must be ignored."""
    b = Builder(threshold=610, offset=96)
    b.cycle([0, 800, 801], [99999, 5, 5])                 # root cycle, excl total 10
    # keep the root cycle edge (0->800) and add reachable fan-out + traps
    b.nodes[0][2].extend([100, 200, 300, 400, 500, DANGLING])
    # TRUE ANSWER: reachable 2-cycle totalling EXACTLY the threshold (610)
    b.cycle([100, 101], [305, 305])
    # island with a negative member: 400 + (-100) = 300 (< 610, excluded)
    b.cycle([200, 201], [400, -100])
    # just under threshold: 600 -> excluded
    b.cycle([300, 301], [300, 300])
    # another sub-threshold island
    b.cycle([400, 401], [250, 250])
    # reachable singleton total 500 (< 610, excluded)
    b.add(500, 500, [DANGLING])
    # unreachable island total 20000 (bigger, over threshold, but unreachable)
    b.cycle([950, 951, 952, 953], [5000, 5000, 5000, 5000])
    return b


def build_heldout_3():
    """threshold 10000, ~1900 nodes. Answer is a dense reachable SCC totalling
    12000; a 200-node count trap totals 11800; an unreachable SCC totals 30000;
    a 1600-long reachable chain makes recursive DFS die at the default limit;
    plus a batch of sub-threshold reachable islands."""
    b = Builder(threshold=10000, offset=96)
    rng = _lcg(4242)

    # root in a 3-cycle (its value excluded) that also fans out to everything
    b.cycle([0, 1, 2], [88888, 7, 8])   # excl-root island total 15 (tiny)
    b.nodes[0][2].extend([100000, 200000, 300000, DANGLING])

    # ---- true answer: a dense reachable SCC of 60 nodes totalling 12000 ----
    ans = list(range(100000, 100060))
    for i, nid in enumerate(ans):
        deps = [ans[(i + 1) % len(ans)]]
        for _ in range(6):
            deps.append(ans[next(rng) % len(ans)])   # cross edges -> dense SCC
        b.add(nid, 200, deps)                         # 60 * 200 = 12000

    # ---- count trap: reachable SCC of 200 nodes but only 11800 total ----
    ct = list(range(200000, 200200))
    for i, nid in enumerate(ct):
        b.add(nid, 59, [ct[(i + 1) % len(ct)]])       # 200 * 59 = 11800 (< 12000)

    # ---- long reachable chain: 1600 singletons -> recursive DFS overflows ----
    chain = 300000
    for k in range(1600):
        nxt = chain + k + 1 if k < 1599 else DANGLING
        b.add(chain + k, 3, [nxt])                    # tiny values, singletons

    # ---- sub-threshold reachable islands (excluded by threshold) ----
    for j in range(20):
        base = 400000 + j * 3
        b.cycle([base, base + 1, base + 2], [1000, 1000, 1000])  # 3000 < 10000
        b.nodes[0][2].append(base)

    # ---- unreachable SCC total 30000 (bigger, over threshold, unreachable) ----
    un = list(range(500000, 500006))
    for i, nid in enumerate(un):
        b.add(nid, 5000, [un[(i + 1) % len(un)]])     # 6 * 5000 = 30000, NOT reachable
    return b


def build_heldout_4():
    """threshold 10000, offset 64. Winner sits EXACTLY at threshold (10000) so a
    strict > drops it; a 9999 island is just under; a larger island (14000) is
    unreachable; a count trap; root in a cycle."""
    b = Builder(threshold=10000, offset=64)
    b.cycle([0, 5, 6], [70000, 11, 12])              # root cycle, excl total 23
    b.nodes[0][2].extend([10, 20, 30, DANGLING])
    # TRUE ANSWER: reachable 2-cycle totalling EXACTLY 10000
    b.cycle([10, 11], [6000, 4000])
    # just under threshold: 9999 -> excluded
    b.cycle([20, 21], [5000, 4999])
    # count trap: 50-node reachable SCC totalling 9500 (> nodes, < 10000 -> excluded too)
    ct = list(range(3000, 3050))
    for i, nid in enumerate(ct):
        b.add(nid, 190, [ct[(i + 1) % len(ct)]])     # 50 * 190 = 9500
    b.nodes[0][2].append(3000)
    # unreachable island 14000 (bigger, over threshold, unreachable)
    b.cycle([950, 951], [7000, 7000])
    return b


def build_heldout_5():
    """threshold 0, offset 96. Winner is a reachable SINGLETON with a large
    value that beats every cycle; a negative-heavy cycle; an unreachable
    positive island; root in a cycle; dangling + self loops."""
    b = Builder(threshold=0, offset=96)
    b.cycle([0, 7, 8], [40000, 30, 40])              # root cycle, excl total 70
    b.nodes[0][2].extend([100, 200, 300, 400, DANGLING, 0])  # self loop on root
    # decoy cycles
    b.cycle([100, 101, 102], [900, 900, 900])        # total 2700
    b.cycle([200, 201], [1600, 1600])                # total 3200
    # negative-heavy reachable cycle: 5000 + (-4000) = 1000
    b.cycle([300, 301], [5000, -4000])
    # TRUE ANSWER: reachable singleton value 3500 (beats every cycle above)
    b.add(400, 3500, [DANGLING, 400])                # self loop, still one node
    # unreachable positive island 9000
    b.cycle([950, 951, 952], [3000, 3000, 3000])
    return b


BUILDERS = {
    "scene": build_scene,
    "heldout_1": build_heldout_1,
    "heldout_2": build_heldout_2,
    "heldout_3": build_heldout_3,
    "heldout_4": build_heldout_4,
    "heldout_5": build_heldout_5,
}


def generate_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, fn in BUILDERS.items():
        data = fn().pack()
        open(os.path.join(outdir, name + ".mcfg"), "wb").write(data)
    return list(BUILDERS)


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    for name in generate_all(outdir):
        print(f"wrote {outdir}/{name}.mcfg")
