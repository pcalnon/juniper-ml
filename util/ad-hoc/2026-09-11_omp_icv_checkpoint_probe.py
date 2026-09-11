#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- PF-8 follow-up
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

WHAT THIS IS
------------
The instrument for the two residuals left open by
``notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-LIBRARY-ATTRIBUTION.md`` §7:

1. **§7 residual 1 / §5.3 -- what ENDS the burst after the initial output pass.** Measured
   twice (listener census and one-process ``--mode fit --on-thread``), unexplained, and NOT a
   re-pin by either of cascor's two ``set_num_threads`` sites.
2. **§7 residual 2 / §5.1 -- which PyTorch path runs 16-wide off the constructor thread while a
   plain matmul does not.**

It also converts §5's step 2 -- "``omp_set_num_threads`` binds the calling thread", flagged in
that note as **the one INFERRED link in the chain** -- from an appeal to the OpenMP spec into a
direct measurement.

THE INSTRUMENT
--------------
libgomp is already mapped into the process (the native profile puts 47.6% of samples there), so
``omp_get_max_threads()`` is callable through ``ctypes`` -- and it returns the **calling
thread's** ``nthreads-var`` ICV. That is the width that thread will actually use for its next
parallel region, which is exactly the quantity every previous probe had to infer.

``torch.get_num_threads()`` cannot answer this and never could: it reports the library-global
setting. Worse -- and this probe's first draft learned it the hard way -- **calling that getter
is not a passive read**. It runs torch's per-thread lazy init and RE-PINS the calling thread's
ICV, so a checkpoint that read it would terminate the burst it was built to observe. Every
checkpoint here is therefore ICV-only by default; ``--mode torch-getter-side-effect`` is the
standing two-arm proof of that side effect, and the ``icv-map`` do-nothing control arm is what
catches a regression into it.

WHY A FRESH THREAD PER ARM
--------------------------
Once a thread has been re-pinned it STAYS re-pinned, so running several op classes on one
thread would let the first one mask every later one -- the "a broken thing masks the next one"
failure class. Every ``icv-map`` arm therefore gets its own newly-created thread.

WHY THE SAMPLER IS STILL HERE
-----------------------------
An ICV reading is a statement about what a thread *would* do. The burst is a statement about
what the process *did*. Quoting the first as though it settled the second would be an
instrument answering an adjacent question, so the concurrent thread census is retained and the
ICV transition is reported against the observed burn, not instead of it.

HOW TO RUN
----------
The three BLAS variables are read once at library load, so unpinning is the CALLER's job::

    env -C /home/pcalnon/Development/python/Juniper/juniper-cascor/src \
        -u OMP_NUM_THREADS -u MKL_NUM_THREADS -u OPENBLAS_NUM_THREADS \
        /opt/miniforge3/envs/JuniperCascor1/bin/python \
        <this script> --mode icv-map --json /path/out.json

    env -C ... <same> <this script> --mode growth --max-iterations 3 --json /path/out.json

``env(1)`` stops accepting options at the first ``NAME=VALUE``, so every ``-u`` must precede
every assignment (trap 1 of the 2026-09-10 handoff).

WHAT IT DOES NOT DO
-------------------
- It does not modify juniper-cascor. The growth-mode checkpoints are installed by wrapping
  bound methods on the instance for the duration of the run.
- Its wall-clock and core figures are NOT run-tier numbers; they are taken at ambient load and
  are not comparable to a suite cell (§7 residual 3 of the attribution note).
- The spiral is generated locally at ``radius_scale`` 10.0. A unit-radius spiral is degenerate
  for candidate training -- every tanh candidate sits in its linear regime and ``grow_network``
  terminates with zero hidden units (§7 residual 4).
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

# ---------------------------------------------------------------------------------------------
# libgomp ICV access
# ---------------------------------------------------------------------------------------------


class Gomp:
    """Handle to the ALREADY-LOADED libgomp.

    ``dlopen`` on a soname that is already mapped returns a handle to that same mapping, so this
    reads the ICVs of the runtime torch is actually using rather than a second copy. The
    ``maps_entry`` recorded alongside every result is the evidence for that claim -- do not drop
    it, it is the only thing separating this from "some libgomp says 16".
    """

    def __init__(self) -> None:
        self.lib = ctypes.CDLL("libgomp.so.1")
        self.lib.omp_get_max_threads.restype = ctypes.c_int
        self.lib.omp_get_max_threads.argtypes = []
        self.lib.omp_get_num_procs.restype = ctypes.c_int
        self.lib.omp_get_num_procs.argtypes = []

    def max_threads(self) -> int:
        """The CALLING THREAD's nthreads-var ICV."""
        return int(self.lib.omp_get_max_threads())

    def num_procs(self) -> int:
        return int(self.lib.omp_get_num_procs())

    @staticmethod
    def maps_entry() -> str | None:
        try:
            with open("/proc/self/maps", "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if "libgomp" in line:
                        return line.rstrip("\n").split()[-1]
        except OSError:
            return None
        return None


def checkpoint(gomp: Gomp, label: str, store: list[dict[str, object]], touch_torch: bool = False) -> dict[str, object]:
    """Record the calling thread's ICV and identity.

    ``touch_torch`` DEFAULTS TO FALSE AND MUST STAY THAT WAY on any checkpoint that precedes a
    measurement. ``torch.get_num_threads()`` is not a passive read: it runs torch's per-thread
    lazy init and RE-PINS the calling thread's ICV. A checkpoint that called it would end the
    very burst it exists to observe, and the first draft of this probe did exactly that -- every
    ``icv-map`` arm, including the do-nothing control, reported a 16 -> 8 re-pin caused by the
    instrument rather than by the op. ``--mode torch-getter-side-effect`` is the standing proof.
    """
    entry: dict[str, object] = {
        "label": label,
        "t": round(time.perf_counter() - _T0, 4),
        "thread_name": threading.current_thread().name,
        "tid": threading.get_native_id(),
        "omp_icv_max_threads": gomp.max_threads(),
    }
    if touch_torch:
        import torch

        entry["torch_get_num_threads"] = torch.get_num_threads()
        entry["torch_read_is_itself_a_repin"] = True
    store.append(entry)
    return entry


_T0 = time.perf_counter()


# ---------------------------------------------------------------------------------------------
# Thread census -- what the process actually DID
# ---------------------------------------------------------------------------------------------


def read_thread_cpu() -> dict[int, tuple[str, float]]:
    """Per-thread (comm, cpu_seconds) from /proc/self/task/<tid>/stat fields 14/15."""
    ticks = os.sysconf("SC_CLK_TCK")
    out: dict[int, tuple[str, float]] = {}
    try:
        tids = os.listdir("/proc/self/task")
    except OSError:
        return out
    for raw in tids:
        try:
            tid = int(raw)
        except ValueError:
            continue
        try:
            with open(f"/proc/self/task/{tid}/stat", "r", encoding="utf-8", errors="replace") as handle:
                data = handle.read()
        except OSError:
            continue
        close = data.rfind(")")
        if close < 0:
            continue
        comm = data[data.find("(") + 1 : close]
        fields = data[close + 2 :].split()
        # After the comm field, stat field 14 (utime) is index 11 and 15 (stime) index 12.
        if len(fields) < 13:
            continue
        try:
            cpu = (int(fields[11]) + int(fields[12])) / ticks
        except ValueError:
            continue
        out[tid] = (comm, cpu)
    return out


class ThreadSampler(threading.Thread):
    """Samples how many threads are actually burning, so the ICV story is checked against it."""

    def __init__(self, interval: float, busy_fraction: float = 0.5) -> None:
        super().__init__(name="icv-sampler", daemon=True)
        self.interval = interval
        self.busy_fraction = busy_fraction
        self.samples: list[dict[str, object]] = []
        self._stop = threading.Event()

    def run(self) -> None:
        prev = read_thread_cpu()
        prev_wall = time.perf_counter()
        while not self._stop.is_set():
            self._stop.wait(self.interval)
            now = read_thread_cpu()
            wall = time.perf_counter()
            dt = wall - prev_wall
            if dt <= 0:
                prev, prev_wall = now, wall
                continue
            busy = 0
            cores = 0.0
            for tid, (comm, cpu) in now.items():
                if comm == "icv-sampler":
                    continue
                before = prev.get(tid)
                if before is None:
                    continue
                delta = cpu - before[1]
                cores += delta / dt
                if delta / dt >= self.busy_fraction:
                    busy += 1
            self.samples.append(
                {"t": round(wall - _T0, 4), "busy_threads": busy, "cores": round(cores, 3), "alive_threads": len(now)}
            )
            prev, prev_wall = now, wall

    def stop(self) -> None:
        self._stop.set()


# ---------------------------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------------------------


def make_spiral(n_spirals: int, n_points: int, n_rotations: float, noise: float, seed: int, radius_scale: float = 10.0):
    """A two-spiral set at the cell's parameters, generated locally (see module docstring)."""
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


def spiral_tensors(seed: int = 20260807):
    """The cell's 320 training rows, as tensors."""
    import numpy as np
    import torch

    x_np, y_np = make_spiral(2, 200, 2.0, 0.05, seed)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(x_np))
    keep = order[: int(0.8 * len(x_np))]
    return torch.from_numpy(x_np[keep]), torch.from_numpy(y_np[keep])


# ---------------------------------------------------------------------------------------------
# Mode: icv-map -- which op class re-pins a fresh thread?
# ---------------------------------------------------------------------------------------------


def run_icv_map(gomp: Gomp, args: argparse.Namespace) -> dict[str, object]:
    """Each arm on its OWN fresh thread: read the ICV, run one op class, read it again."""
    import torch

    x, y = spiral_tensors()

    def _op_none() -> None:
        return None

    def _op_matmul() -> None:
        a = torch.randn(512, 512)
        b = torch.randn(512, 512)
        total = float((a @ b)[0, 0])
        _SINK.append(total)

    def _op_linear_fwd() -> None:
        layer = torch.nn.Linear(2, 2)
        with torch.no_grad():
            out = layer(x)
        _SINK.append(float(out[0, 0]))

    def _op_linear_bwd() -> None:
        layer = torch.nn.Linear(2, 2)
        opt = torch.optim.SGD(layer.parameters(), lr=0.01)
        for _ in range(args.bwd_steps):
            opt.zero_grad()
            loss = torch.nn.functional.mse_loss(layer(x), y)
            loss.backward()
            opt.step()
        _SINK.append(float(loss.detach()))

    # Constructed ON THE MAIN THREAD, exactly as the service does (`_create_network_locked` runs
    # on the request thread). Building it inside the arm would put the constructor's
    # `torch.set_num_threads(2)` on the arm's own thread and the arm would then measure the
    # constructor pin rather than the pass -- which is what the first draft of this arm did.
    prebuilt = _build_network(args, output_epochs=args.map_epochs)

    def _op_output_pass_prebuilt() -> None:
        prebuilt.train_output_layer(x, y, args.map_epochs)

    def _op_construct_here() -> None:
        built = _build_network(args, output_epochs=args.map_epochs)
        _SINK.append(float(built.output_epochs))

    # The note's own §5.1 op shape (a SUSTAINED 1500x1500 loop), not a single small matmul --
    # a one-shot 512x512 is not the thing §5.1 measured and must not be quoted as if it were.
    def _op_matmul_note_shape() -> None:
        a = torch.rand(1500, 1500)
        b = a.clone()
        end = time.perf_counter() + args.burn_seconds
        total = 0.0
        while time.perf_counter() < end:
            total += float((a @ b)[0, 0])
        _SINK.append(total)

    # The mechanism candidate for `_collect_worker_results`: the parent reconstructs the
    # workers' tensors as it drains the result queue.
    def _op_unpickle_tensor() -> None:
        import pickle  # noqa: PLC0415 -- local to the arm

        blob = pickle.dumps(torch.randn(64, 64))
        restored = pickle.loads(blob)  # noqa: S301 -- our own bytes, not untrusted input
        _SINK.append(float(restored[0, 0]))

    def _op_from_numpy() -> None:
        import numpy as np  # noqa: PLC0415 -- local to the arm

        restored = torch.from_numpy(np.zeros((64, 64), dtype=np.float32))
        _SINK.append(float(restored[0, 0]))

    ops = {
        "none": _op_none,
        "matmul": _op_matmul,
        "matmul_note_shape": _op_matmul_note_shape,
        "linear_fwd": _op_linear_fwd,
        "linear_bwd": _op_linear_bwd,
        "output_pass": _op_output_pass_prebuilt,
        "unpickle_tensor": _op_unpickle_tensor,
        "from_numpy": _op_from_numpy,
        "construct_here": _op_construct_here,
    }

    arms: list[dict[str, object]] = []
    for name, op in ops.items():
        record: list[dict[str, object]] = []
        error: list[str] = []

        def _arm(op=op, name=name, record=record, error=error) -> None:
            checkpoint(gomp, f"{name}:entry", record)
            started = time.perf_counter()
            try:
                op()
            except Exception as exc:  # noqa: BLE001 -- an arm that dies must not kill the map
                error.append(f"{type(exc).__name__}: {exc}")
            elapsed = time.perf_counter() - started
            checkpoint(gomp, f"{name}:after", record)
            record.append({"label": f"{name}:elapsed_s", "elapsed_s": round(elapsed, 4)})

        sampler = ThreadSampler(interval=0.1)
        sampler.start()
        thread = threading.Thread(target=_arm, name=f"icvmap-{name}")
        thread.start()
        thread.join()
        sampler.stop()
        sampler.join(timeout=5.0)

        # The ICV says what the thread WOULD use; peak_busy_threads says what the process DID.
        # Reporting only the first would be an instrument answering an adjacent question.
        peak_busy = max((sample["busy_threads"] for sample in sampler.samples), default=0)
        peak_cores = max((sample["cores"] for sample in sampler.samples), default=0.0)

        entry = {
            "op": name,
            "icv_on_entry": record[0]["omp_icv_max_threads"],
            "icv_after": record[1]["omp_icv_max_threads"],
            "repinned": record[0]["omp_icv_max_threads"] != record[1]["omp_icv_max_threads"],
            "peak_busy_threads": peak_busy,
            "peak_cores": peak_cores,
            "samples": len(sampler.samples),
            "elapsed_s": record[2]["elapsed_s"],
            "checkpoints": record,
        }
        if error:
            entry["error"] = error[0]
        arms.append(entry)

    return {"mode": "icv-map", "arms": arms, "control_arm_must_not_repin": "none"}


# ---------------------------------------------------------------------------------------------
# Mode: torch-getter-side-effect -- the standing proof that reading the getter re-pins
# ---------------------------------------------------------------------------------------------


def run_getter_side_effect(gomp: Gomp, args: argparse.Namespace) -> dict[str, object]:
    """Two fresh threads, identical except that one calls ``torch.get_num_threads()``.

    This is the control that separates "the op re-pinned the thread" from "the instrument
    re-pinned the thread". Without it the icv-map is uninterpretable, because the first draft's
    checkpoint called the getter and every arm re-pinned identically.
    """
    import torch

    arms: list[dict[str, object]] = []

    for name, touch in (("read_icv_twice", False), ("read_getter_between", True)):
        out: dict[str, object] = {"arm": name, "calls_torch_get_num_threads": touch}

        def _arm(touch=touch, out=out) -> None:
            out["icv_first"] = gomp.max_threads()
            if touch:
                out["torch_get_num_threads"] = torch.get_num_threads()
            out["icv_second"] = gomp.max_threads()

        thread = threading.Thread(target=_arm, name=f"getter-{name}")
        thread.start()
        thread.join()
        out["repinned"] = out["icv_first"] != out["icv_second"]
        arms.append(out)

    return {"mode": "torch-getter-side-effect", "arms": arms}


_SINK: list[float] = []


# ---------------------------------------------------------------------------------------------
# Mode: growth -- where in the growth loop does the ICV drop?
# ---------------------------------------------------------------------------------------------


def _build_network(args: argparse.Namespace, output_epochs: int | None = None):
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
        output_epochs=args.output_epochs if output_epochs is None else output_epochs,
        candidate_epochs=args.candidate_epochs,
        worker_thread_count=1,
    )
    return CascadeCorrelationNetwork(config=config)


def run_growth(gomp: Gomp, args: argparse.Namespace) -> dict[str, object]:
    """Run the real growth loop on a worker thread, checkpointing the ICV around each stage.

    The network is CONSTRUCTED on the main thread and TRAINED on a worker, which is the shape
    the service takes (``_create_network_locked`` on the request thread, ``_run_training`` on
    the ``cascor-train`` executor).
    """
    x, y = spiral_tensors()
    record: list[dict[str, object]] = []

    checkpoint(gomp, "main:before_construction", record)
    network = _build_network(args)
    checkpoint(gomp, "main:after_construction", record)

    # Wrap the three growth-loop stages. Bound-method wrappers run ON the training thread, which
    # is the only place the ICV that matters can be read.
    def _wrap(method_name: str):
        original = getattr(network, method_name)

        def wrapper(*a, **kw):
            checkpoint(gomp, f"{method_name}:before", record)
            try:
                return original(*a, **kw)
            finally:
                checkpoint(gomp, f"{method_name}:after", record)

        return original, wrapper

    # The four documented steps of ``train_candidates`` are wrapped too, so the re-pin can be
    # bisected to a step rather than attributed to the method as a whole. A name that is not
    # present on this build is skipped, which keeps the probe usable across cascor revisions --
    # but see ``wrapped_methods`` in the result: a step missing from that list was NOT measured,
    # and an absent checkpoint must never be read as "this step did not re-pin".
    stages = (
        "train_output_layer",
        "train_candidates",
        "_retrain_output_layer",
        "_prepare_candidate_input",
        "_compute_hidden_outputs",
        "_generate_candidate_tasks",
        "_calculate_optimal_process_count",
        "_execute_candidate_training",
        "_execute_parallel_training",
        "_execute_sequential_training",
        "_ensure_worker_pool",
        "_drain_stale_results",
        "_cleanup_pending_shared_memory",
        "_collect_worker_results",
        "_collect_training_results",
        # Wrapped to interleave a checkpoint immediately AFTER each `result_queue.get()`:
        # `_collect_training_results` is a get/validate loop, so a `_validate_training_result`
        # checkpoint that already reads 2 puts the re-pin in the unpickling of the worker's
        # payload rather than in the validation.
        "_validate_training_result",
        "_process_training_results",
    )
    originals = {}
    for name in stages:
        if not hasattr(network, name):
            continue
        original, wrapper = _wrap(name)
        originals[name] = original
        setattr(network, name, wrapper)

    outcome: dict[str, object] = {}

    def _train() -> None:
        checkpoint(gomp, "train_thread:entry", record)
        started = time.perf_counter()
        try:
            network.fit(x, y)
            outcome["ok"] = True
        except Exception as exc:  # noqa: BLE001 -- record the failure, do not lose the trace
            outcome["ok"] = False
            outcome["error"] = f"{type(exc).__name__}: {exc}"
        outcome["elapsed_s"] = round(time.perf_counter() - started, 3)
        checkpoint(gomp, "train_thread:exit", record)

    sampler = ThreadSampler(interval=args.interval)
    sampler.start()
    thread = threading.Thread(target=_train, name="cascor-train-probe")
    thread.start()
    thread.join(timeout=args.timeout)
    timed_out = thread.is_alive()
    sampler.stop()
    sampler.join(timeout=5.0)

    for name, original in originals.items():
        setattr(network, name, original)

    # ``hidden_units`` is a LIST on this build; an earlier draft read a scalar
    # ``current_hidden_units`` that does not exist and reported its -1 default as though it
    # were a measurement. Report None when the attribute is absent rather than a sentinel that
    # reads like a count.
    units = getattr(network, "hidden_units", None)
    hidden = len(units) if isinstance(units, list) else None

    return {
        "mode": "growth",
        "timed_out": timed_out,
        "outcome": outcome,
        "hidden_units": hidden,
        "wrapped_methods": sorted(originals),
        "not_wrapped_absent_on_this_build": sorted(set(stages) - set(originals)),
        "checkpoints": record,
        "samples": sampler.samples,
    }


# ---------------------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=("icv-map", "growth", "torch-getter-side-effect"), default="icv-map")
    parser.add_argument("--json", type=Path, default=None, help="write the full result as JSON here")
    parser.add_argument("--interval", type=float, default=0.2, help="sampler interval, seconds")
    parser.add_argument("--timeout", type=float, default=900.0, help="training-thread join timeout, seconds")
    parser.add_argument("--output-epochs", type=int, default=800, help="growth mode: output_epochs")
    parser.add_argument("--candidate-epochs", type=int, default=60, help="growth mode: candidate_epochs")
    parser.add_argument("--max-iterations", type=int, default=3, help="growth mode: max_iterations")
    parser.add_argument("--candidate-pool-size", type=int, default=4, help="growth mode: candidate_pool_size")
    parser.add_argument("--map-epochs", type=int, default=200, help="icv-map: epochs for the output_pass arm")
    parser.add_argument("--bwd-steps", type=int, default=50, help="icv-map: steps for the linear_bwd arm")
    parser.add_argument("--burn-seconds", type=float, default=4.0, help="icv-map: seconds for the matmul_note_shape arm (the note's sustained shape)")
    args = parser.parse_args()

    sys.path.insert(0, os.getcwd())

    gomp = Gomp()
    pre_import_main_icv = gomp.max_threads()
    num_procs = gomp.num_procs()

    import numpy as np
    import torch

    post_import_main_icv = gomp.max_threads()

    header = {
        "mode": args.mode,
        "blas_env": {
            name: os.environ.get(name)
            for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "CASCOR_NUM_PROCESSES")
        },
        "omp_get_num_procs": num_procs,
        "libgomp_maps_entry": Gomp.maps_entry(),
        "main_icv_before_torch_import": pre_import_main_icv,
        "main_icv_after_torch_import": post_import_main_icv,
        "torch_get_num_threads_after_import": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
        "loadavg": os.getloadavg(),
        "versions": {"torch": torch.__version__, "numpy": np.__version__, "python": sys.version.split()[0]},
        "cwd": os.getcwd(),
    }

    dispatch = {
        "icv-map": run_icv_map,
        "growth": run_growth,
        "torch-getter-side-effect": run_getter_side_effect,
    }
    body = dispatch[args.mode](gomp, args)
    result = {**header, **body}

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # A compact human summary; the JSON is the record.
    print(f"libgomp: {header['libgomp_maps_entry']}  omp_get_num_procs={num_procs}")
    print(f"main-thread ICV: before torch import {pre_import_main_icv} -> after {post_import_main_icv}")
    if args.mode == "icv-map":
        print(f"{'op':<19}{'icv_entry':>10}{'icv_after':>10}{'repinned':>10}{'peak_thr':>9}{'peak_cores':>11}{'elapsed_s':>11}")
        for arm in result["arms"]:
            print(
                f"{arm['op']:<19}{arm['icv_on_entry']:>10}{arm['icv_after']:>10}"
                f"{str(arm['repinned']):>10}{arm['peak_busy_threads']:>9}{arm['peak_cores']:>11}{arm['elapsed_s']:>11}"
            )
            if "error" in arm:
                print(f"    ERROR: {arm['error']}")
        control = next((a for a in result["arms"] if a["op"] == "none"), None)
        if control is not None and control["repinned"]:
            print("  !! CONTROL ARM RE-PINNED -- the instrument is perturbing the measurement; arms are NOT interpretable")
    elif args.mode == "growth":
        print(f"fit outcome: {result['outcome']}  hidden_units={result['hidden_units']}  timed_out={result['timed_out']}")
        print(f"{'checkpoint':<40}{'t':>9}{'icv':>7}  thread")
        for entry in result["checkpoints"]:
            if "omp_icv_max_threads" not in entry:
                continue
            print(f"{entry['label']:<40}{entry['t']:>9}{entry['omp_icv_max_threads']:>7}  {entry['thread_name']}")
        peak = max((s["busy_threads"] for s in result["samples"]), default=0)
        print(f"peak busy threads: {peak}   samples: {len(result['samples'])}")
    if args.mode == "torch-getter-side-effect":
        for arm in result["arms"]:
            print(
                f"{arm['arm']:<22} calls_getter={str(arm['calls_torch_get_num_threads']):<6} "
                f"icv {arm['icv_first']} -> {arm['icv_second']}   repinned={arm['repinned']}"
            )
    if args.json:
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
