#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- owner decision D1 (the epoch-count debt)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md §5.2

Does a BLAS thread cap move cascor's EPOCH COUNTS? This is the debt the D1 flip is gated on.

WHY THIS EXISTS
---------------
The owner ruled D1's repair on 2026-09-23 as "pay the debt, then flip": change
``configure_blas_threads()``'s default from "do nothing" to 2, but ONLY IF the cap does not move
the epoch count. Both the D1 and D2 gates asked for **epoch counts per phase**. The 09-16 arm
(``2026-09-16_thread_width_arm.py``, left untouched as the provenance of its evidence) emitted
**stage** counts, so "cascor#531's penalty does not reproduce" rested on wall time alone. #531's
second channel was the COUNT: a cap changes BLAS reduction order, so floating-point results, so
where a patience-based loop stops.

A SECOND DEFECT IN THE 09-16 MEASUREMENT, FOUND BUILDING THIS ONE
-----------------------------------------------------------------
Its structural counts were **budget-bound**, so they could not have moved. ``max_iterations=4``
grew exactly 4 hidden units in all 39 arms. The output loop, ``for epoch in range(epochs)`` in
``train_output_layer``, has no early exit, so output epochs always equal the request. A count
that equals its budget cannot show a count channel. That is the D6 lesson: budgets 10 and 50
assert the request back to itself.

WHAT THIS DOES DIFFERENTLY
--------------------------
* **Per-phase counts.** Every ``train_candidates`` call's ``TrainingResults.epochs_completed``
  (one per candidate: the emergent, patience-bound count), the epochs requested of every output
  pass (budget-bound by construction, reported as such), hidden units grown, and the history
  length ``fit`` returns.
* **A budget check per arm.** Each phase reports whether its count hit its budget. **A
  budget-bound phase is reported as NON-DISCRIMINATING and gives no verdict**, instead of being
  counted as a pass.
* **A positive control.** The ``seed`` arm changes only the network's ``random_seed``, with the
  same data and the same width. If it changes the counts the instrument can see a count change,
  and an unchanged count across widths is then evidence rather than an insensitive instrument.
  If it does NOT change them, the verdict is VACUOUS.
* **Interleaved, seeded order**, as the 09-16 driver did. The counts are load-insensitive, but
  the wall-clock columns are not, and randomising costs nothing.

THE ARMS (all ``worker_thread_count=1``, so candidate workers pin to 1 thread regardless)
-----------------------------------------------------------------------------------------
``none``        today's default: no BLAS variables. The constructor pins only the constructing
                thread to 2, and the training thread runs its first output pass at the runtime
                default until it is re-pinned.
``env2``        THE FLIP: OMP/MKL/OPENBLAS_NUM_THREADS=2 in the environment before torch loads.
                This is exactly what the new default would produce.
``env16``       the same route at 16, the widest this host offers.
``thread16``    ``torch.set_num_threads(16)`` on the training thread; the other route.
``seed``        ``none`` with a different network ``random_seed``: the positive control.

**VERDICT for the flip**: the flip is clear when ``env2`` reproduces ``none`` exactly on every
emergent count, in every repeat, AND the ``seed`` arm differs from ``none`` on at least one of
them. Other outcomes are reported as what they are: MOVED, VACUOUS, or NONDETERMINISTIC (repeats
of one arm disagree).

Usage (from anywhere; the cascor tree is an argument)::

    python3 util/ad-hoc/2026-09-23_d1_epoch_count_sweep.py \
        --cascor-src /path/to/juniper-cascor/src --out-dir ~/.local/state/juniper-experiments/suites/d1-epoch-debt-<date>

``--arm`` is internal: the driver re-invokes this file once per arm, in a fresh process, because
the ``env`` arms must set the variables before torch is imported.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import random
import subprocess
import sys
import threading
import time
from pathlib import Path

BLAS_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")

# arm -> (mechanism, width, network random_seed override or None)
ARMS = {
    "none": ("none", 0, None),
    "env2": ("env", 2, None),
    "env16": ("env", 16, None),
    "thread16": ("thread", 16, None),
    "seed": ("none", 0, 7),
}


# ------------------------------------------------------------------------------------------------
# One arm, in its own process
# ------------------------------------------------------------------------------------------------
class Gomp:
    """The already-loaded libgomp; omp_get_max_threads() reads the CALLING THREAD's width."""

    def __init__(self) -> None:
        self.lib = ctypes.CDLL("libgomp.so.1")
        self.lib.omp_get_max_threads.restype = ctypes.c_int
        self.lib.omp_get_max_threads.argtypes = []

    def width(self) -> int:
        return int(self.lib.omp_get_max_threads())


def make_spiral(n_spirals: int, n_points: int, n_rotations: float, noise: float, seed: int, radius_scale: float = 10.0):
    """Verbatim from 2026-09-16_thread_width_arm.py: radius 10.0 (a unit-radius spiral grows nothing)."""
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


def run_arm(args: argparse.Namespace) -> int:
    mechanism, width, random_seed = ARMS[args.arm]
    sys.path.insert(0, os.getcwd())
    gomp = Gomp()
    observed_env = {name: os.environ.get(name) for name in BLAS_VARS}

    import numpy as np
    import torch

    from cascade_correlation.cascade_correlation import CascadeCorrelationNetwork
    from cascade_correlation.cascade_correlation_config.cascade_correlation_config import CascadeCorrelationConfig

    config_kwargs = dict(
        input_size=2,
        output_size=2,
        max_hidden_units=args.max_hidden_units,
        candidate_pool_size=args.candidate_pool_size,
        max_iterations=args.max_iterations,
        output_epochs=args.output_epochs,
        candidate_epochs=args.candidate_epochs,
        worker_thread_count=1,
    )
    if random_seed is not None:
        config_kwargs["random_seed"] = random_seed
    config = CascadeCorrelationConfig(**config_kwargs)
    network = CascadeCorrelationNetwork(config=config)
    # Read on MAIN only, where a re-pin is harmless (the constructor already pinned this thread).
    global_after_construction = torch.get_num_threads()

    x_np, y_np = make_spiral(2, 200, 2.0, 0.05, args.data_seed)
    order = np.random.default_rng(args.data_seed).permutation(len(x_np))
    keep = order[: int(0.8 * len(x_np))]
    x, y = torch.from_numpy(x_np[keep]), torch.from_numpy(y_np[keep])

    output_passes: list[dict] = []
    candidate_phases: list[dict] = []
    t0 = time.perf_counter()
    original_train_output = network.train_output_layer
    original_train_candidates = network.train_candidates

    def train_output_wrapper(*a, **kw):
        # The executed count equals the request: the loop is `for epoch in range(epochs)` with no
        # early exit. So record the REQUEST, resolved exactly as the method resolves it.
        requested = kw.get("epochs", a[2] if len(a) > 2 else None)
        started = time.perf_counter()
        icv_in = gomp.width()
        try:
            return original_train_output(*a, **kw)
        finally:
            output_passes.append({"epochs_requested": requested, "seconds": round(time.perf_counter() - started, 4), "icv_in": icv_in, "t_start": round(started - t0, 4)})

    def train_candidates_wrapper(*a, **kw):
        started = time.perf_counter()
        icv_in = gomp.width()
        result = original_train_candidates(*a, **kw)
        per_candidate = getattr(result, "epochs_completed", None)
        if not isinstance(per_candidate, list):
            per_candidate = [per_candidate]
        candidate_phases.append(
            {
                "epochs_completed": [int(e) for e in per_candidate if e is not None],
                "best_candidate_id": getattr(result, "best_candidate_id", None),
                "best_correlation": round(float(getattr(result, "best_correlation", 0.0) or 0.0), 10),
                "seconds": round(time.perf_counter() - started, 4),
                "icv_in": icv_in,
                "t_start": round(started - t0, 4),
            }
        )
        return result

    network.train_output_layer = train_output_wrapper
    network.train_candidates = train_candidates_wrapper

    outcome: dict = {}

    def _train() -> None:
        if mechanism == "thread":
            torch.set_num_threads(width)
        outcome["icv_at_train_entry"] = gomp.width()
        # Never call torch.get_num_threads() here: it re-pins the calling thread (ICV note §1.1).
        started = time.perf_counter()
        try:
            history = network.fit(x, y)
            outcome["ok"] = True
            outcome["history_train_loss_len"] = len(history.get("train_loss", [])) if isinstance(history, dict) else None
            final = history.get("train_loss", [None])[-1] if isinstance(history, dict) and history.get("train_loss") else None
            outcome["final_train_loss"] = round(float(final), 10) if final is not None else None
        except Exception as exc:  # noqa: BLE001 -- record it, do not lose the arm
            outcome["ok"] = False
            outcome["error"] = f"{type(exc).__name__}: {exc}"
        outcome["fit_seconds"] = round(time.perf_counter() - started, 4)
        outcome["icv_at_exit"] = gomp.width()

    thread = threading.Thread(target=_train, name="cascor-train-arm")
    thread.start()
    thread.join()
    network.train_output_layer = original_train_output
    network.train_candidates = original_train_candidates

    units = getattr(network, "hidden_units", None)
    record = {
        "arm": args.arm,
        "mechanism": mechanism,
        "width": width,
        "random_seed_override": random_seed,
        "observed_blas_env": observed_env,
        "torch_global_after_construction": global_after_construction,
        "budgets": {
            "candidate_epochs": args.candidate_epochs,
            "output_epochs": args.output_epochs,
            "max_iterations": args.max_iterations,
            "max_hidden_units": args.max_hidden_units,
        },
        "outcome": outcome,
        "hidden_units": len(units) if isinstance(units, list) else None,
        "candidate_phases": candidate_phases,
        "output_passes": output_passes,
        "loadavg": os.getloadavg(),
        "versions": {"torch": torch.__version__, "numpy": np.__version__, "python": sys.version.split()[0]},
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return 0 if outcome.get("ok") else 1


# ------------------------------------------------------------------------------------------------
# The driver
# ------------------------------------------------------------------------------------------------
def signature(record: dict) -> dict:
    """The COUNTS an arm is compared on -- the owner's criterion. Wall clock is deliberately absent."""
    return {
        "hidden_units": record.get("hidden_units"),
        "candidate_epochs": [p["epochs_completed"] for p in record.get("candidate_phases", [])],
        "output_epochs": [p["epochs_requested"] for p in record.get("output_passes", [])],
        "history_len": record.get("outcome", {}).get("history_train_loss_len"),
    }


def numerics(record: dict) -> dict:
    """SUPPLEMENTARY, not the verdict: which candidate won each phase, and the final loss.

    Counts can survive a numeric change that these do not, so identical numerics is a stronger
    statement than identical counts ("the cap did not touch the arithmetic"), and differing
    numerics with identical counts says the channel exists but did not reach the count at these
    budgets. The flip's criterion is the count; this column explains the count.
    """
    return {
        "best_candidate_ids": [p["best_candidate_id"] for p in record.get("candidate_phases", [])],
        "best_correlations": [p["best_correlation"] for p in record.get("candidate_phases", [])],
        "final_train_loss": record.get("outcome", {}).get("final_train_loss"),
    }


def budget_binding(records: list[dict], budgets: dict) -> dict:
    """Which phases' counts are PINNED to their budget in the control arm (and so cannot move)."""
    cands = [e for r in records for p in r.get("candidate_phases", []) for e in p["epochs_completed"]]
    units = {r.get("hidden_units") for r in records}
    return {
        "candidate_all_at_budget": bool(cands) and all(e >= budgets["candidate_epochs"] for e in cands),
        "candidate_share_below_budget": round(sum(e < budgets["candidate_epochs"] for e in cands) / len(cands), 3) if cands else None,
        "hidden_units_at_budget": units <= {min(budgets["max_iterations"], budgets["max_hidden_units"])},
        "output_epochs": "budget-bound BY CONSTRUCTION (no early exit in train_output_layer)",
    }


def drive(args: argparse.Namespace) -> int:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    arm_names = args.arms
    rng = random.Random(args.order_seed)  # noqa: S311 -- reproducible ordering, not secrecy
    extra = [
        "--candidate-epochs", str(args.candidate_epochs),
        "--output-epochs", str(args.output_epochs),
        "--max-iterations", str(args.max_iterations),
        "--max-hidden-units", str(args.max_hidden_units),
        "--candidate-pool-size", str(args.candidate_pool_size),
        "--data-seed", str(args.data_seed),
    ]  # fmt: skip
    records: list[dict] = []
    for rep in range(args.repeats):
        order = arm_names[:]
        rng.shuffle(order)
        print(f"[debt] repeat {rep + 1}/{args.repeats}: {order}", flush=True)
        for arm in order:
            mechanism, width, _ = ARMS[arm]
            env = dict(os.environ)
            for name in BLAS_VARS:
                env.pop(name, None)
            if mechanism == "env":
                for name in BLAS_VARS:
                    env[name] = str(width)
            out_json = args.out_dir / f"r{rep}-{arm}.json"
            cmd = [args.python, str(Path(__file__).resolve()), "--arm", arm, "--json", str(out_json), *extra]
            started = time.perf_counter()
            proc = subprocess.run(cmd, cwd=str(args.cascor_src), env=env, capture_output=True, text=True, check=False)  # noqa: S603
            if not out_json.is_file():
                rec = {"arm": arm, "failed": True, "returncode": proc.returncode, "stderr": proc.stderr[-600:]}
            else:
                rec = json.loads(out_json.read_text(encoding="utf-8"))
            rec["repeat"] = rep
            rec["driver_seconds"] = round(time.perf_counter() - started, 3)
            records.append(rec)
            sig = signature(rec) if not rec.get("failed") else None
            print(f"[debt]   r{rep}-{arm}: " + ("FAILED rc=%s %s" % (rec.get("returncode"), rec.get("stderr", "")[-200:]) if sig is None else f"units={sig['hidden_units']} cand={sig['candidate_epochs']} fit={rec['outcome'].get('fit_seconds')}s"), flush=True)

    budgets = {"candidate_epochs": args.candidate_epochs, "output_epochs": args.output_epochs, "max_iterations": args.max_iterations, "max_hidden_units": args.max_hidden_units}
    ok = [r for r in records if not r.get("failed") and r.get("outcome", {}).get("ok")]
    by_arm: dict[str, list[dict]] = {}
    for r in ok:
        by_arm.setdefault(r["arm"], []).append(r)
    sigs = {arm: [json.dumps(signature(r), sort_keys=True) for r in rs] for arm, rs in by_arm.items()}

    nondeterministic = sorted(arm for arm, ss in sigs.items() if len(set(ss)) > 1)
    control = by_arm.get("none", [])
    binding = budget_binding(control, budgets) if control else {}
    control_sig = sigs.get("none", [None])[0]
    differs = {arm: (ss[0] != control_sig) for arm, ss in sigs.items() if arm != "none" and ss}
    emergent_available = bool(binding) and not (binding["candidate_all_at_budget"] and binding["hidden_units_at_budget"])

    if len(ok) != len(records):
        verdict = "INCOMPLETE -- some arms failed; no verdict"
    elif "none" not in sigs or "env2" not in sigs or "seed" not in sigs:
        verdict = "INCOMPLETE -- the none / env2 / seed arms are all required for a verdict"
    elif not emergent_available:
        verdict = "NON-DISCRIMINATING -- every count is pinned to its budget; raise the budgets"
    elif nondeterministic:
        verdict = f"NONDETERMINISTIC -- repeats disagree within {nondeterministic}; an exact comparison is unsafe"
    elif not differs.get("seed"):
        verdict = "VACUOUS -- the seed control did not move the counts, so an unchanged count proves nothing"
    elif differs.get("env2"):
        verdict = "MOVED -- the cap changes the counts; the flip is NOT cleared"
    else:
        verdict = "CLEAR -- env2 reproduces the default exactly and the seed control moves; the flip is cleared"

    nums = {arm: [json.dumps(numerics(r), sort_keys=True) for r in rs] for arm, rs in by_arm.items()}
    control_num = nums.get("none", [None])[0]
    numerics_identical_to_control = {arm: (ns[0] == control_num) for arm, ns in nums.items() if arm != "none" and ns}
    numerics_deterministic = {arm: len(set(ns)) == 1 for arm, ns in nums.items()}

    summary = {
        "verdict": verdict,
        "budgets": budgets,
        "budget_binding_in_control": binding,
        "nondeterministic_arms": nondeterministic,
        "differs_from_control": differs,
        "numerics_identical_to_control": numerics_identical_to_control,
        "numerics_deterministic": numerics_deterministic,
        "signatures": {arm: json.loads(ss[0]) for arm, ss in sigs.items()},
        "numerics": {arm: json.loads(ns[0]) for arm, ns in nums.items()},
        "order_seed": args.order_seed,
        "cascor_src": str(args.cascor_src),
        "records": records,
    }
    (args.out_dir / "debt.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print()
    print(f"budget binding in control: {json.dumps(binding)}")
    for arm in arm_names:
        if arm in sigs:
            print(f"  {arm:<9} n={len(sigs[arm])} counts_deterministic={len(set(sigs[arm])) == 1} counts_differ_from_none={differs.get(arm, '-')} numerics_deterministic={numerics_deterministic.get(arm)} numerics_identical_to_none={numerics_identical_to_control.get(arm, '-')}")
    print(f"\nVERDICT: {verdict}\nwrote {args.out_dir / 'debt.json'}")
    return 0 if verdict.startswith("CLEAR") else 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--arm", choices=sorted(ARMS), default=None, help="internal: run ONE arm in this process")
    parser.add_argument("--json", type=Path, default=None, help="internal: where --arm writes its record")
    parser.add_argument("--arms", nargs="+", choices=sorted(ARMS), default=["none", "env2", "env16", "thread16", "seed"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--order-seed", type=int, default=20260923)
    parser.add_argument("--cascor-src", type=Path, default=Path("/home/pcalnon/Development/python/Juniper/juniper-cascor/src"))
    parser.add_argument("--python", default="/opt/miniforge3/envs/JuniperCascor1/bin/python")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--candidate-epochs", type=int, default=400)
    parser.add_argument("--output-epochs", type=int, default=800)
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--max-hidden-units", type=int, default=10)
    parser.add_argument("--candidate-pool-size", type=int, default=4)
    parser.add_argument("--data-seed", type=int, default=20260807, help="the 09-16 arm's seed, so the data is the same")
    args = parser.parse_args()
    if args.arm:
        if args.json is None:
            parser.error("--arm needs --json")
        return run_arm(args)
    if args.out_dir is None:
        parser.error("--out-dir is required when driving")
    return drive(args)


if __name__ == "__main__":
    raise SystemExit(main())
