"""Sample per-thread CPU of a pid twice, 3 s apart, and print the busiest threads. Read-only. Scratch only."""

import os
import sys
import time

pid = sys.argv[1]


def sample():
    out = {}
    for tid in os.listdir(f"/proc/{pid}/task"):
        try:
            with open(f"/proc/{pid}/task/{tid}/stat") as fh:
                fields = fh.read().rsplit(")", 1)[1].split()
            with open(f"/proc/{pid}/task/{tid}/comm") as fh:
                comm = fh.read().strip()
            out[tid] = (int(fields[11]) + int(fields[12]), fields[0], comm)
        except OSError:
            pass  # the thread exited between listdir() and the read; skip it
    return out


a = sample()
time.sleep(3)
b = sample()
rows = sorted(((b[t][0] - a.get(t, (0,))[0], t, b[t][1], b[t][2]) for t in b), reverse=True)[:6]
for delta, tid, state, comm in rows:
    print(f"tid={tid} state={state} comm={comm} jiffies_in_3s={delta}")
