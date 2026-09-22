#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- owner decision D6
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md

D6: is ``epochs_completed`` stable enough to gate on equality?

WHY THIS EXISTS TWICE
---------------------
This measurement was already taken once, on 2026-09-17
(``~/.local/state/juniper-experiments/suites/d6-epochs-spread-20260917/spread.json``), by an
instrument that **does** survive — ``2026-09-17_epochs_completed_spread.py``, untracked in the
sibling worktree ``.claude/worktrees/optimized-giggling-koala``, alongside a note reaching the
same conclusion. That session obeyed every placement rule and simply **never committed**, so to
``git``, to CI and to this session's first searches the work did not exist.

This file therefore is NOT a recovery of lost work. It exists to put the answer on a committed,
re-runnable footing, and it adds the two things the 09-17 instrument lacks: the OpenMP ICV
actually in force at each cell (so an inert axis is distinguishable from a real invariance) and
a do-nothing control (so instrument perturbation is visible rather than assumed).

Full account, including the search that missed the earlier work, is in
``notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md`` §1.

WHAT IS MEASURED, AND WHY THIS EXACT SHAPE
------------------------------------------
``juniper-cascor/src/tests/performance/test_micro_candidate.py::TestCandidateEpochScaling``
is the *only* one of the five cascor micro files whose work is emergent rather than fixed
(``JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`` §D6). Its
``test_epoch_scaling`` seeds ``torch.manual_seed(42)``, builds a 2-input candidate over 100
samples, and calls ``train_detailed`` at budgets 10/50/100/200. This instrument reproduces that
construction **exactly** — same seed, same shapes, same call — because a gate is only as
meaningful as its agreement with the thing gated. A nearby-but-different setup would answer an
adjacent question.

The axis added on top is THREAD WIDTH. D6's blocker was that round 1 saw requested-100 land on
52 and round 2 on 68, and the suspected cause was ambient load. But the causal story in
``…SIX-OWNER-DECISIONS-RULED.md`` §1 is numeric, not temporal: thread count changes BLAS
reduction order, hence floating-point results, hence where a patience-based loop stops. If that
is what moved 52 -> 68, **width** is the variable to sweep, and load is a red herring.

THE INSTRUMENT HAZARD THIS LANE ALREADY PAID FOR TWICE
------------------------------------------------------
``torch.get_num_threads()`` is NOT a passive read: it runs torch's per-thread lazy init and
RE-PINS the calling thread. It destroyed the 2026-09-11 ``icv-map`` run (every arm, including
the do-nothing control, reported an identical instrument-caused re-pin) and then destroyed the
2026-09-16 width sweep six days later, in the same lane, after the hazard had been written into
a note AND into project memory. Width is therefore read here **only** through
``ctypes.CDLL("libgomp.so.1").omp_get_max_threads()``, which mutates nothing, and the libgomp
path is recorded with the readings so a result is never "some libgomp said N".

A do-nothing CONTROL arm runs first and last. If the control's two readings disagree, the
instrument is perturbing the measurement and no arm in the run is interpretable.

USAGE
-----
    cd /home/pcalnon/Development/python/Juniper/juniper-cascor/src
    python3 <this file> --json ~/.local/state/juniper-experiments/suites/d6-.../spread.json

Run from cascor's ``src/`` — the import is ``candidate_unit.candidate_unit``, exactly as the
test does it. Read-only with respect to the cascor tree.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import sys
from pathlib import Path

DEFAULT_WIDTHS = (1, 2, 4, 8, 16)
DEFAULT_EPOCHS = (10, 50, 100, 200)


class Gomp:
    """The already-loaded libgomp. ``omp_get_max_threads()`` reads the CALLING thread's width.

    libgomp is already mapped into this process by torch, so ``CDLL`` returns a handle to that
    same mapping rather than loading a second copy -- which is why the reading describes the
    process actually doing the work.
    """

    def __init__(self) -> None:
        self.lib = ctypes.CDLL("libgomp.so.1")
        self.lib.omp_get_max_threads.restype = ctypes.c_int
        self.lib.omp_get_max_threads.argtypes = []

    def width(self) -> int:
        return int(self.lib.omp_get_max_threads())

    @staticmethod
    def mapped_path() -> "str | None":
        """The libgomp actually mapped in, from /proc/self/maps -- never assumed."""
        try:
            with open("/proc/self/maps", encoding="utf-8") as handle:
                for line in handle:
                    if "libgomp.so" in line:
                        return line.rstrip().split()[-1]
        except OSError:
            return None
        return None


def _observe(gomp: Gomp, torch_mod) -> dict:
    """One reading of the thread state. Deliberately does NOT call torch.get_num_threads()."""
    return {"icv": gomp.width(), "loadavg": os.getloadavg()[0], "torch_interop": torch_mod.get_num_interop_threads()}


def main() -> int:
    parser = argparse.ArgumentParser(description="D6: epochs_completed spread", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--widths", type=int, nargs="+", default=list(DEFAULT_WIDTHS))
    parser.add_argument("--epochs", type=int, nargs="+", default=list(DEFAULT_EPOCHS))
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--n-samples", type=int, default=100)
    parser.add_argument("--input-size", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42, help="the seed test_micro_candidate uses")
    parser.add_argument("--learning-rate", type=float, default=0.005)
    # An explicit path rather than an implicit cwd. The sibling arms use `os.getcwd()` and so
    # must be launched from cascor's src/; that is a silent failure mode (run it from the wrong
    # directory and the import error names `candidate_unit`, not the mistake), and it is
    # awkward from a worktree-isolated session whose command classifier refuses `cd X && ...`
    # chains. Defaults to the ecosystem-standard location.
    parser.add_argument("--cascor-src", type=Path, default=Path("/home/pcalnon/Development/python/Juniper/juniper-cascor/src"))
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    if not (args.cascor_src / "candidate_unit").is_dir():
        print(f"--cascor-src does not look like a cascor checkout: {args.cascor_src}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(args.cascor_src))
    import torch  # noqa: E402  - after the cwd insert, exactly as the cascor arms do

    from candidate_unit.candidate_unit import CandidateUnit  # noqa: E402

    gomp = Gomp()

    def one(epochs: int) -> int:
        """test_micro_candidate's ``run()``, verbatim in construction and call."""
        torch.manual_seed(args.seed)
        x = torch.randn(args.n_samples, args.input_size)
        residual = torch.randn(args.n_samples, 2)
        torch.manual_seed(args.seed)
        candidate = CandidateUnit(CandidateUnit__input_size=args.input_size, CandidateUnit__activation_function=torch.nn.Tanh())
        result = candidate.train_detailed(x=x, epochs=epochs, residual_error=residual, learning_rate=args.learning_rate, display_frequency=0)
        return int(result.epochs_completed)

    # The control runs BEFORE any set_num_threads call and again at the end. Its job is to make
    # instrument perturbation visible rather than to produce a datum.
    control_before = _observe(gomp, torch)
    control_epochs_before = one(args.epochs[-1])

    observations: "dict[str, list[int]]" = {}
    icv_in_force: "dict[str, int]" = {}
    for width in args.widths:
        torch.set_num_threads(width)
        for epochs in args.epochs:
            key = f"w{width}-e{epochs}"
            icv_in_force[key] = gomp.width()
            observations[key] = [one(epochs) for _ in range(args.repeats)]

    control_epochs_after = one(args.epochs[-1])
    control_after = _observe(gomp, torch)

    spreads = {key: (max(values) - min(values)) for key, values in observations.items()}
    by_epochs: "dict[str, set]" = {}
    for key, values in observations.items():
        by_epochs.setdefault(key.split("-")[1], set()).update(values)

    payload = {
        "instrument": Path(__file__).name,
        "widths": args.widths,
        "epochs": args.epochs,
        "repeats": args.repeats,
        "seed": args.seed,
        "observations": observations,
        "icv_in_force": icv_in_force,
        "spread_within_cell": spreads,
        "max_spread_within_cell": max(spreads.values()) if spreads else None,
        "distinct_values_per_budget": {budget: sorted(values) for budget, values in by_epochs.items()},
        "control": {
            "epochs_before": control_epochs_before,
            "epochs_after": control_epochs_after,
            "stable": control_epochs_before == control_epochs_after,
            "observed_before": control_before,
            "observed_after": control_after,
        },
        "libgomp": Gomp.mapped_path(),
        "blas_env": {name: os.environ.get(name) for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "loadavg": os.getloadavg(),
        "versions": {"torch": torch.__version__, "python": sys.version.split()[0], "platform": platform.platform()},
    }

    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n")
    print(text)

    # The verdict is printed, never encoded in the exit status: a spread is a finding either way,
    # and an instrument that exits non-zero on "the answer was interesting" gets wrapped in a
    # `|| true` by the first caller that hits it.
    if not payload["control"]["stable"]:
        print("\nCONTROL UNSTABLE — the instrument is perturbing the measurement; no arm is interpretable.", file=sys.stderr)
    elif payload["max_spread_within_cell"] == 0:
        print("\nVERDICT: zero spread within every cell — exact-match is safe on this host/config.", file=sys.stderr)
    else:
        print(f"\nVERDICT: max within-cell spread {payload['max_spread_within_cell']} — exact-match would be FLAKY.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
