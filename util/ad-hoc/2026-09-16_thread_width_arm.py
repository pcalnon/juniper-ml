#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- owner decisions D1 and D2
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

ONE ARM of the thread-width sweep. Runs a single cascor `fit()` at a single width, by a single
mechanism, and emits JSON. The driver (`2026-09-16_thread_width_sweep.py`) runs the matrix.

WHAT THE TWO OWNER DECISIONS ASK
--------------------------------
**D1**: the whole arc has assumed width 2 is right for the output passes, because that is what
cascor's constructor formula `max(2, worker_thread_count * 2)` happens to produce. 16 is measured
to be pathological; **that does not establish 2 as optimal**. Sweep 2/4/6/8/10/16 and look at the
LATER passes, which are the ones that actually run at the re-pinned width.

**D2**: the owner ruled the `runtime:` block should be implemented by exporting the BLAS
variables. cascor#531 measured that route costing the candidate phase **1.52x** — but BOTH of its
channels shrink as the budget rises (throughput 1.26x -> 1.14x, epoch count 1.21x -> 1.03x), so
1.52x is the worst case at a TIGHT cap, not a flat tax. The question is therefore *at which cap
does the cost become acceptable*, which needs a sweep of values, on current code, with BOTH
phases measured.

Both are the same measurement with a different knob, so this is one instrument with `--mechanism`.

THE MECHANISM DIFFERENCE, WHICH IS THE WHOLE POINT
--------------------------------------------------
``thread``  ``torch.set_num_threads(W)`` on the training thread. Sets torch's GLOBAL and pins the
            calling thread. Does **not** reach the candidate workers: they are separate processes
            that set their own width at ``cascade_correlation.py:4153`` from
            ``worker_thread_count``.
``env``     ``OMP/MKL/OPENBLAS_NUM_THREADS=W`` in the process environment, read once at BLAS load.
            Inherited by every ``forkserver`` child, so it DOES reach the candidate workers. This
            is the route that carries cascor#531's penalty.
``none``    control: touch neither. The constructor's own ``set_num_threads(2)`` is all that runs.

``env`` must be set BEFORE this process imports torch, so the driver puts it in the subprocess
environment; this script only records what it sees and never sets it (setting it after import
would be a silent no-op and would make the arm a lie).

WHY THE GLOBAL MATTERS FOR ``thread``
-------------------------------------
Setting only the *calling thread's* ICV would not survive: the training thread is re-pinned to
**torch's global** during the first candidate result collection
(``JUNIPER_2026-09-11_..._ICV-INSTRUMENT.md`` §3.5). ``torch.set_num_threads`` sets the global too,
so the re-pin re-applies W rather than reverting to 2 — and the per-stage ICV readings below are
what prove it actually held, rather than assuming it.

WHAT IT REPORTS, AND WHY NOT ms/epoch
-------------------------------------
Per stage: wall seconds, and the ICV in force on the training thread. Plus epochs completed and
the final accuracy. **Compare arms on TOTAL WALL and EPOCH COUNT, never on ms/epoch** — cascor#531's
epoch-count channel means a width that is faster per epoch can run more epochs and lose. That is
the same discipline as `step_count` in the run tier.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
import threading
import time
from pathlib import Path

BLAS_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")


class Gomp:
    """The already-loaded libgomp; omp_get_max_threads() reads the CALLING THREAD's width."""

    def __init__(self) -> None:
        self.lib = ctypes.CDLL("libgomp.so.1")
        self.lib.omp_get_max_threads.restype = ctypes.c_int
        self.lib.omp_get_max_threads.argtypes = []

    def width(self) -> int:
        return int(self.lib.omp_get_max_threads())


def make_spiral(n_spirals: int, n_points: int, n_rotations: float, noise: float, seed: int, radius_scale: float = 10.0):
    """Local spiral at radius 10.0 — a UNIT-radius spiral grows zero hidden units."""
    import numpy as np

    rng = np.random.default_rng(seed)
    xs, ys = [], []
    for spiral in range(n_spirals):
        t = np.linspace(0.0, 1.0, n_points)
        angle = 2.0 * np.pi * n_rotations * t + (2.0 * np.pi * spiral / n_spirals)
        radius = t * radius_scale
        x = radius * np.cos(angle) + rng.normal(0.0, noise, n_points)
        y = radius * np.sin(angle) + rng.normal(0.0, noise, n_points)
        xs.append(np.stack([x, y], axis=1))
        label = np.zeros((n_points, n_spirals), dtype=np.float32)
        label[:, spiral] = 1.0
        ys.append(label)
    return np.concatenate(xs).astype(np.float32), np.concatenate(ys).astype(np.float32)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--width", type=int, required=True, help="thread width for this arm")
    parser.add_argument("--mechanism", choices=("thread", "env", "none"), required=True)
    parser.add_argument("--output-epochs", type=int, default=800)
    parser.add_argument("--candidate-epochs", type=int, default=60)
    parser.add_argument("--max-iterations", type=int, default=4)
    parser.add_argument("--candidate-pool-size", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260807)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    sys.path.insert(0, os.getcwd())
    gomp = Gomp()
    observed_env = {name: os.environ.get(name) for name in BLAS_VARS}

    import numpy as np
    import torch

    from cascade_correlation.cascade_correlation import CascadeCorrelationNetwork
    from cascade_correlation.cascade_correlation_config.cascade_correlation_config import (
        CascadeCorrelationConfig,
    )

    config = CascadeCorrelationConfig(
        input_size=2,
        output_size=2,
        max_hidden_units=10,
        candidate_pool_size=args.candidate_pool_size,
        max_iterations=args.max_iterations,
        output_epochs=args.output_epochs,
        candidate_epochs=args.candidate_epochs,
        worker_thread_count=1,
    )
    # Constructed on MAIN, as the service does (_create_network_locked on the request thread).
    network = CascadeCorrelationNetwork(config=config)
    # Read the global HERE, on the main thread, where re-pinning is harmless (the constructor has
    # already pinned this thread to 2). Reading it on the training thread would destroy the arm.
    global_after_construction = torch.get_num_threads()
    main_icv_after_construction = gomp.width()

    x_np, y_np = make_spiral(2, 200, 2.0, 0.05, args.seed)
    rng = np.random.default_rng(args.seed)
    order = rng.permutation(len(x_np))
    keep = order[: int(0.8 * len(x_np))]
    x, y = torch.from_numpy(x_np[keep]), torch.from_numpy(y_np[keep])

    stages: list[dict] = []
    t0 = time.perf_counter()

    def _wrap(name: str):
        original = getattr(network, name)

        def wrapper(*a, **kw):
            started = time.perf_counter()
            icv_in = gomp.width()
            try:
                return original(*a, **kw)
            finally:
                stages.append(
                    {
                        "stage": name,
                        "t_start": round(started - t0, 4),
                        "seconds": round(time.perf_counter() - started, 4),
                        "icv_in": icv_in,
                        "icv_out": gomp.width(),
                    }
                )

        return original, wrapper

    originals = {}
    for name in ("train_output_layer", "_retrain_output_layer", "train_candidates"):
        if hasattr(network, name):
            originals[name], wrapper = _wrap(name)
            setattr(network, name, wrapper)

    outcome: dict = {}

    def _train() -> None:
        # The mechanism is applied HERE, on the training thread, before any work.
        # `thread` sets torch's global as well as this thread's ICV — which is what makes the
        # width survive the candidate-collection re-pin (see module docstring).
        if args.mechanism == "thread":
            torch.set_num_threads(args.width)
        outcome["icv_at_train_entry"] = gomp.width()
        # ⚠ DO NOT read torch.get_num_threads() here. It is NOT a passive read: it runs torch's
        # per-thread lazy init and RE-PINS the calling thread to the global
        # (JUNIPER_2026-09-11_..._ICV-INSTRUMENT.md §1.1). The first version of this arm called it
        # on this line and thereby re-pinned every `env` and `none` arm to the constructor's 2
        # BEFORE any training ran -- silently converting the entire D2 half of the sweep into a
        # measurement of the instrument. It was invisible in the `thread` arms, because there
        # set_num_threads(W) has already made the global W, so the getter re-pins to the value
        # that was wanted anyway. A defect that only corrupts SOME arms is the dangerous kind.
        # The global is recorded once, from the MAIN thread, before this thread is created.
        started = time.perf_counter()
        try:
            network.fit(x, y)
            outcome["ok"] = True
        except Exception as exc:  # noqa: BLE001 — record it, do not lose the arm
            outcome["ok"] = False
            outcome["error"] = f"{type(exc).__name__}: {exc}"
        outcome["fit_seconds"] = round(time.perf_counter() - started, 4)
        outcome["icv_at_exit"] = gomp.width()

    thread = threading.Thread(target=_train, name="cascor-train-arm")
    thread.start()
    thread.join()
    for name, original in originals.items():
        setattr(network, name, original)

    units = getattr(network, "hidden_units", None)
    initial = [s for s in stages if s["stage"] == "train_output_layer"]
    later = [s for s in stages if s["stage"] == "_retrain_output_layer"]
    candidates = [s for s in stages if s["stage"] == "train_candidates"]

    result = {
        "width": args.width,
        "mechanism": args.mechanism,
        "observed_blas_env": observed_env,
        "torch_global_after_construction": global_after_construction,
        "main_icv_after_construction": main_icv_after_construction,
        "outcome": outcome,
        "hidden_units": len(units) if isinstance(units, list) else None,
        # D1's target: the LATER passes. Reported as a total, because comparing arms on a
        # per-epoch figure is exactly what cascor#531's epoch-count channel defeats.
        "initial_pass_seconds": round(sum(s["seconds"] for s in initial), 4),
        "later_passes_seconds": round(sum(s["seconds"] for s in later), 4),
        "later_pass_count": len(later),
        "candidate_seconds": round(sum(s["seconds"] for s in candidates), 4),
        "candidate_phase_count": len(candidates),
        "stages": stages,
        "loadavg": os.getloadavg(),
        "versions": {"torch": torch.__version__, "numpy": np.__version__, "python": sys.version.split()[0]},
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "stages"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
