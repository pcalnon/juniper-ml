"""Scratch CPU-contention generator (agent-s): spin N busy processes for T seconds.

Usage: python3 cpu_burn.py <n_procs> <seconds>
"""

import multiprocessing as mp
import sys
import time


def spin(deadline):
    x = 0
    while time.time() < deadline:
        x = (x * 1103515245 + 12345) & 0xFFFFFFFF


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else mp.cpu_count()
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    deadline = time.time() + secs
    procs = [mp.Process(target=spin, args=(deadline,)) for _ in range(n)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    print(f"cpu_burn: {n} procs x {secs}s done")
