#!/usr/bin/env python3
"""
Does `torch.set_num_threads(2)` bound a CPU matmul's core usage when the BLAS environment variables are unset? Measure it in a child process, per environment, from /proc/self/stat.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-10
Status: ad-hoc — investigation (perf lane P2 item 4.1 residue: why the cascor listener drew ~11 cores during its INITIAL output pass under the default budget and ~2 under the pinned one)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md

WHY THIS EXISTS

cascor's parent process calls `torch.set_num_threads(max(2, worker_thread_count * 2))`
(`cascade_correlation.py:1179-1180`, from the constructor) and its service tier deliberately
leaves OMP/MKL/OPENBLAS unset (`parallelism/blas_threads.py`). The occupancy probe measured the
listener at ~11 cores during the INITIAL output-layer pass with the variables unset and ~2 with
them exported at 2 (the ten later passes run at ~2 either way). This isolates what the pin can
and cannot bound: the same matmul loop, in a fresh interpreter, with and without the variables,
after `torch.set_num_threads(2)`, reporting cpu-seconds per wall-second. It shows WHICH pool the
variables reach; it does not identify which library the listener's burst runs in, and its loop
counts are host-load-sensitive (one run 57 vs 79, a re-run 94 vs 85).

    /opt/miniforge3/envs/JuniperCascor1/bin/python util/ad-hoc/2026-09-10_torch_thread_pin_probe.py
"""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - launches this file's own child mode with a fixed interpreter
import sys

CHILD_CODE = r"""
import json, os, sys, time
import torch
def cpu_ticks():
    with open('/proc/self/stat') as fh:
        rest = fh.read().rsplit(')', 1)[1].split()
    return int(rest[11]) + int(rest[12])
clk = os.sysconf('SC_CLK_TCK')
pin = int(sys.argv[1])
if pin > 0:
    torch.set_num_threads(pin)
n = int(sys.argv[2]); seconds = float(sys.argv[3]); lib = sys.argv[4]
if lib == "numpy":
    import numpy as np
    a = np.random.rand(n, n).astype(np.float32); b = np.random.rand(n, n).astype(np.float32)
    op = lambda: a @ b  # noqa: E731
else:
    a = torch.randn(n, n); b = torch.randn(n, n)
    op = lambda: torch.mm(a, b)  # noqa: E731
op()  # warm
t0 = time.time(); c0 = cpu_ticks(); loops = 0
while time.time() - t0 < seconds:
    op(); loops += 1
wall = time.time() - t0; cpu = (cpu_ticks() - c0) / clk
print(json.dumps({"lib": lib, "set_num_threads": pin, "get_num_threads": torch.get_num_threads(), "loops": loops, "wall_s": round(wall, 3), "cpu_s": round(cpu, 3), "cpu_per_wall": round(cpu / wall, 2), "env": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")}, "torch": torch.__version__}))
"""


def run_child(env_extra: dict, pin: int, lib: str = "torch", n: int = 1024, seconds: float = 2.0) -> dict:
    env = {**os.environ, **env_extra}
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        if key not in env_extra:
            env.pop(key, None)
    out = subprocess.run([sys.executable, "-c", CHILD_CODE, str(pin), str(n), str(seconds), lib], capture_output=True, text=True, env=env, check=True)  # nosec B603
    return json.loads(out.stdout.strip().splitlines()[-1])


PINNED = {"OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2"}


def main() -> int:
    cases = [
        ("torch  unset, no set_num_threads", {}, 0, "torch"),
        ("torch  unset, set_num_threads(2)", {}, 2, "torch"),
        ("torch  OMP/MKL/OPENBLAS=2, set_num_threads(2)", PINNED, 2, "torch"),
        ("torch  OMP/MKL/OPENBLAS=2, no set_num_threads", PINNED, 0, "torch"),
        ("numpy  unset, no set_num_threads", {}, 0, "numpy"),
        ("numpy  unset, torch.set_num_threads(2)", {}, 2, "numpy"),
        ("numpy  OMP/MKL/OPENBLAS=2", PINNED, 0, "numpy"),
    ]
    for label, env_extra, pin, lib in cases:
        result = run_child(env_extra, pin, lib)
        print(f"{label:48s} torch.get_num_threads={result['get_num_threads']:2d}  cpu/wall={result['cpu_per_wall']:5.2f}  loops={result['loops']}  ({result['torch']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
