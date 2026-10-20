#!/usr/bin/env python3
"""
Concurrent torch BLAS calls from several Python threads: does this env livelock?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — investigation (turing bring-up task E2; a negative result, see below)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.3 E-BLAS);
         conf/hosts/turing/conda-envs/JuniperCanopy1.yml; util/ad-hoc/2026-10-19_turing_e2_validate_envs.py

Why: juniper-canopy's unit lane hung on turing in the JuniperCanopy1 env at
src/tests/unit/frontend/test_stage2_global_lane.py, with `--timeout=60` never firing. A `sample` of the
process showed three threads spinning in OpenBLAS 0.3.30's `blas_memory_alloc`: the main thread
(torch linear -> addmm -> sgemm) and two demo-mode `_training_loop` daemon threads left running by
earlier tests (matmul -> mv -> sgemv, and linear -> sgemm). This script tries that shape without
canopy. Each worker thread runs float32 `linear` and matrix-vector products, the same BLAS entry
points, and the main thread waits with a deadline.

Result, 2026-10-20: it does NOT reproduce the hang. Both modes finish in JuniperCanopy1 (OpenBLAS
0.3.30, openmp build) and in JuniperCascor1 (MKL), with and without OMP_NUM_THREADS. canopy's own
unit lane is the reproducer: it hung at the same test in two runs, and with OMP_NUM_THREADS=6, so
that every thread's OpenMP count equals torch's default, it ran to the end. The trigger needs more
than concurrent small BLAS calls. The script is kept as the record of what did not reproduce it
(plan §18.3 E-BLAS).

Run it with an env's own interpreter, isolated from the worktree:

    /usr/local/miniforge3/envs/<Env>/bin/python3.14 -I util/ad-hoc/2026-10-20_turing_e2_blas_concurrency_repro.py
    /usr/local/miniforge3/envs/<Env>/bin/python3.14 -I util/ad-hoc/2026-10-20_turing_e2_blas_concurrency_repro.py --threads 1

`--mode uniform` (the default) builds each worker's tensors inside the worker. That runs ops
which initialise torch's per-thread OpenMP count, so every thread agrees on one count.
`--mode mixed` gives the shape the hang had. The main thread builds the tensors and the workers
only call BLAS. Worker 0 first calls torch.get_num_threads(), which sets its OpenMP count to
torch's intra-op default. The other workers never do, so they keep OpenMP's default. Each OpenBLAS
call from a thread whose omp_get_max_threads() differs from OpenBLAS's process-wide count calls
goto_set_num_threads, and those calls race.

Exit 0: every thread finished its iterations. Exit 2: a thread missed the deadline. The stuck
threads are inside native code, so the script leaves through os._exit.
"""

import argparse
import os
import sys
import threading
import time


def _blas_line(torch):
    for line in torch.__config__.show().splitlines():
        line = line.strip()
        if line.startswith("- BLAS_INFO") or "BLAS_INFO=" in line:
            for part in line.replace(",", " ").split():
                if part.startswith("BLAS_INFO="):
                    return part
    return "BLAS_INFO=?"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--threads", type=int, default=3, help="concurrent BLAS callers (default 3, the hang's count)")
    parser.add_argument("--iterations", type=int, default=20000, help="iterations per thread (default 20000)")
    parser.add_argument("--deadline", type=float, default=60.0, help="seconds before the run counts as hung (default 60)")
    parser.add_argument("--mode", choices=("uniform", "mixed"), default="uniform", help="see the module docstring")
    args = parser.parse_args(argv)

    import torch

    print(f"python {sys.version.split()[0]}  torch {torch.__version__}  {_blas_line(torch)}  torch threads {torch.get_num_threads()}  mode {args.mode}")
    print("env:", {k: os.environ[k] for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS") if k in os.environ})

    done = [0] * args.threads

    def uniform_worker(index):
        torch.manual_seed(index)
        x = torch.randn(64, 16)
        w = torch.randn(32, 16, requires_grad=True)
        b = torch.randn(32, requires_grad=True)
        v = torch.randn(16)
        for _ in range(args.iterations):
            y = torch.nn.functional.linear(x, w, b)  # addmm -> sgemm
            y.sum().backward()
            with torch.no_grad():
                _ = w @ v  # mv -> sgemv
                w.grad = None
                b.grad = None
            done[index] += 1

    tensors = [(torch.randn(64, 16), torch.randn(32, 16), torch.randn(32), torch.randn(16)) for _ in range(args.threads)]

    def mixed_worker(index):
        if index == 0:
            torch.get_num_threads()  # torch's lazy per-thread init: this thread's OpenMP count becomes torch's
        x, w, b, v = tensors[index]
        with torch.no_grad():
            for _ in range(args.iterations):
                _ = torch.nn.functional.linear(x, w, b)  # addmm -> sgemm
                _ = w @ v  # mv -> sgemv
                done[index] += 1

    worker = uniform_worker if args.mode == "uniform" else mixed_worker
    threads = [threading.Thread(target=worker, args=(i,), daemon=True, name=f"blas-{i}") for i in range(args.threads)]
    start = time.monotonic()
    for t in threads:
        t.start()
    deadline = start + args.deadline
    for t in threads:
        t.join(max(0.0, deadline - time.monotonic()))
    elapsed = time.monotonic() - start
    alive = [t.name for t in threads if t.is_alive()]
    print(f"threads {args.threads}  iterations done {done}  elapsed {elapsed:.1f} s")
    if alive:
        before = list(done)
        time.sleep(2.0)
        print(f"HUNG: {alive} still running at the {args.deadline:.0f} s deadline; progress in the next 2 s: {[a - b for a, b in zip(done, before)]}")
        sys.stdout.flush()
        os._exit(2)
    print("OK: every thread finished")
    return 0


if __name__ == "__main__":
    sys.exit(main())
