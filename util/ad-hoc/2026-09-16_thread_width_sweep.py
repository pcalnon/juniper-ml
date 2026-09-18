#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- owner decisions D1 and D2
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Driver for the thread-width sweep. Runs `2026-09-16_thread_width_arm.py` across
widths x mechanisms x repeats, then reduces.

WHY THE ORDER IS RANDOMISED
---------------------------
Every number here is wall-clock, and this host has not been quiet in five sessions (1-minute load
5-20, with a multi-hour `clamscan` competing). Running the arms in matrix order would let ambient
drift correlate perfectly with width: if load happens to climb during the run, the last width
measured looks slowest, and the conclusion is about the `clamscan`.

So the full arm list is shuffled ONCE, with a recorded seed, and each repeat is a fresh shuffle.
Drift then spreads across arms instead of accumulating in one. That is the cheap half of the fix;
the expensive half is repeats, and both are needed. **This does not make a loaded host equal to a
quiet one** — it makes the comparison unbiased, not precise. Report the spread, not just the mean.

WHAT TO COMPARE ON
------------------
**Total wall and epoch/stage counts — never ms/epoch.** cascor#531's epoch-count channel
(1.21x -> 1.03x as the budget rises) means a width that is faster per epoch can run more epochs
and lose. `parallelism/blas_threads.py` documents the mechanism: thread count changes BLAS
reduction order, hence floating-point results, hence where a patience-based early-stopping loop
terminates.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

BLAS_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
ARM = Path(__file__).resolve().parent / "2026-09-16_thread_width_arm.py"


def build_arms(widths: list[int], mechanisms: list[str], include_control: bool) -> list[tuple[int, str]]:
    arms = [(w, m) for m in mechanisms for w in widths]
    if include_control:
        arms.append((0, "none"))  # width is ignored for the control
    return arms


def run_arm(width: int, mechanism: str, cascor_src: Path, python_bin: str, out_dir: Path, tag: str, extra: list[str]) -> dict:
    env = dict(os.environ)
    for name in BLAS_VARS:
        env.pop(name, None)
    if mechanism == "env":
        # Read once at BLAS load, so it MUST be in the environment before the process starts.
        for name in BLAS_VARS:
            env[name] = str(width)
    out_json = out_dir / f"{tag}.json"
    cmd = [python_bin, str(ARM), "--width", str(width), "--mechanism", mechanism, "--json", str(out_json), *extra]
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(cascor_src), env=env, capture_output=True, text=True, check=False)  # noqa: S603
    elapsed = time.perf_counter() - started
    if proc.returncode != 0 or not out_json.is_file():
        return {"width": width, "mechanism": mechanism, "failed": True, "returncode": proc.returncode, "stderr": proc.stderr[-400:], "driver_seconds": round(elapsed, 3)}
    record = json.loads(out_json.read_text(encoding="utf-8"))
    record["driver_seconds"] = round(elapsed, 3)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--widths", type=int, nargs="+", default=[2, 4, 6, 8, 10, 16])
    parser.add_argument("--mechanisms", nargs="+", default=["thread", "env"], choices=["thread", "env"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260916, help="shuffle seed, recorded in the output")
    parser.add_argument("--no-control", action="store_true", help="omit the untouched-default control arm")
    parser.add_argument("--cascor-src", type=Path, default=Path("/home/pcalnon/Development/python/Juniper/juniper-cascor/src"))
    parser.add_argument("--python", default="/opt/miniforge3/envs/JuniperCascor1/bin/python")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--output-epochs", type=int, default=800)
    parser.add_argument("--max-iterations", type=int, default=4)
    args, unknown = parser.parse_known_args()

    extra = ["--output-epochs", str(args.output_epochs), "--max-iterations", str(args.max_iterations), *unknown]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)  # noqa: S311 -- reproducible ordering, not secrecy

    arms = build_arms(args.widths, args.mechanisms, not args.no_control)
    records: list[dict] = []
    for rep in range(args.repeats):
        order = arms[:]
        rng.shuffle(order)
        print(f"[sweep] repeat {rep + 1}/{args.repeats}: {[(w, m) for w, m in order]}", flush=True)
        for width, mechanism in order:
            tag = f"r{rep}-{mechanism}-w{width}"
            rec = run_arm(width, mechanism, args.cascor_src, args.python, args.out_dir, tag, extra)
            rec["repeat"] = rep
            records.append(rec)
            status = "FAILED" if rec.get("failed") else f"fit={rec['outcome'].get('fit_seconds')}s later={rec.get('later_passes_seconds')}s icv={rec['outcome'].get('icv_at_exit')}"
            print(f"[sweep]   {tag}: {status}", flush=True)

    summary = args.out_dir / "sweep.json"
    summary.write_text(json.dumps({"seed": args.seed, "arms": arms, "records": records}, indent=2), encoding="utf-8")

    print(f"\n{'mechanism':<10}{'width':>6}{'n':>4}{'later_s med':>13}{'later_s spread':>16}{'fit_s med':>11}{'cand_s med':>12}{'icv_held':>10}")
    for mechanism in sorted({r.get("mechanism") for r in records if not r.get("failed")}):
        for width in sorted({r["width"] for r in records if r.get("mechanism") == mechanism and not r.get("failed")}):
            arm = [r for r in records if r.get("mechanism") == mechanism and r["width"] == width and not r.get("failed")]
            if not arm:
                continue
            later = [r["later_passes_seconds"] for r in arm]
            fit = [r["outcome"]["fit_seconds"] for r in arm]
            cand = [r["candidate_seconds"] for r in arm]
            icvs = {r["outcome"].get("icv_at_exit") for r in arm}
            spread = f"{min(later):.3f}-{max(later):.3f}"
            held = str(sorted(x for x in icvs if x is not None))
            print(f"{mechanism:<10}{width:>6}{len(arm):>4}{statistics.median(later):>13.3f}{spread:>16}{statistics.median(fit):>11.3f}{statistics.median(cand):>12.3f}{held:>10}")

    failed = [r for r in records if r.get("failed")]
    if failed:
        print(f"\n{len(failed)} FAILED arms:")
        for r in failed[:5]:
            print(f"  w={r['width']} {r['mechanism']}: rc={r['returncode']} {r['stderr'][:160]}")
    print(f"\nwrote {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
