#!/usr/bin/env python3
"""
Run juniper-data's CI unit lane, or the 44 tests it used to deselect, under a chosen interpreter, and log it.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4, owner ruling 17: "data: 44 unrun tests")
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (prove the newly selected tests pass, and are not timing-sensitive)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 17 is recorded in the record-update PR)

MODES
    lane     ci.yml's unit-tests step verbatim (juniper-data main 272ff615): -m "unit and not slow"
             juniper_data/tests/unit --verbose --timeout=60 --maxfail=5 --junitxml --cov=juniper_data and the four
             --cov-report forms, every report redirected into --out; then the aggregate gate
             ``coverage report --fail-under=80``. ``--main-selection`` adds a --deselect per newly marked class,
             which reproduces main's selection on the fixed tree (the collect helper proves the sets equal).
    new44    the four newly marked classes only, under the lane's -m and --timeout, -p no:randomly, --durations=0.
    file     all of test_security.py under the lane's -m and --timeout.
    repeat   new44 --runs times, at most --workers at once (default 20 and 4); one log per run plus a summary JSON.

Every run: ``-p no:cacheprovider``, PYTHONDONTWRITEBYTECODE=1 and COVERAGE_FILE under --out, so the worktree gains
no cache, bytecode or .coverage. TMPDIR is left exactly as the session gave it.

Usage:
    python3 <this> --worktree <juniper-data worktree> --out <dir> --mode <mode> [--python <interp>] [--tag <t>]
                   [--main-selection] [--runs N] [--workers W]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: a chosen interpreter running pytest / coverage
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DEFAULT_PYTHON = "/opt/miniforge3/envs/JuniperData/bin/python"
SEC = "juniper_data/tests/unit/test_security.py"
NEW_CLASSES = ("TestAPIKeyAuth", "TestRateLimiter", "TestSecurityModuleFunctions", "TestApiKeysSettingsValidator")
LANE_SEL = ["-m", "unit and not slow"]
# Bordered (``== 44 passed in 4s ==``, at -v) or bare (``44 passed in 4s``, at addopts' -q). Never add a second
# -q: at -qq pytest prints no summary line at all.
SUMMARY_RE = re.compile(r"^=*\s*(\d+ (?:passed|failed|error|skipped|deselected).*?|no tests ran.*?)\s*=*$")


def _summary(text: str) -> str:
    hits = [m.group(1) for ln in text.splitlines() if (m := SUMMARY_RE.match(ln.strip()))]
    return hits[-1] if hits else "<no summary line>"


def _run(argv: list[str], cwd: Path, env: dict[str, str], log: Path) -> tuple[int, str, float]:
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(f"$ (cwd={cwd}) {' '.join(argv)}\n")
        fh.flush()
        proc = subprocess.run(argv, cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT, check=False)  # nosec B603
        elapsed = time.monotonic() - start
        fh.write(f"\n[exit {proc.returncode}] [{elapsed:.1f}s]\n")
    with open(log, encoding="utf-8") as fh:
        text = fh.read()
    return proc.returncode, _summary(text), elapsed


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", required=True, choices=["lane", "new44", "file", "repeat"])
    ap.add_argument("--python", default=DEFAULT_PYTHON)
    ap.add_argument("--tag", default="")
    ap.add_argument("--main-selection", action="store_true")
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    wt, out = args.worktree.resolve(), args.out.resolve()
    name = f"{args.mode}{args.tag}"
    run_dir = out / "runs" / name
    run_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "COVERAGE_FILE": str(run_dir / ".coverage")}
    base = [args.python, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-p", "no:randomly"]
    new44 = [f"{SEC}::{c}" for c in NEW_CLASSES]
    result: dict = {"mode": args.mode, "tag": args.tag, "python": args.python, "worktree": str(wt)}

    if args.mode == "lane":
        argv = base + LANE_SEL + [
            "juniper_data/tests/unit", "--verbose", "--timeout=60", "--maxfail=5",
            f"--junitxml={run_dir / 'junit-unit.xml'}", "--cov=juniper_data", "--cov-report=term-missing",
            f"--cov-report=xml:{run_dir / 'coverage.xml'}", f"--cov-report=html:{run_dir / 'htmlcov'}",
            f"--cov-report=json:{run_dir / 'coverage.json'}",
        ]
        if args.main_selection:
            argv += [f"--deselect={n}" for n in new44]
        rc, summ, secs = _run(argv, wt, env, out / "logs" / f"{name}.log")
        result.update({"exit": rc, "summary": summ, "seconds": round(secs, 1), "log": str(out / "logs" / f"{name}.log")})
        gate = [args.python, "-B", "-m", "coverage", "report", "--fail-under=80"]
        grc, _, _ = _run(gate, wt, env, out / "logs" / f"{name}_coverage_gate.log")
        with open(out / "logs" / f"{name}_coverage_gate.log", encoding="utf-8") as fh:
            total = [ln for ln in fh.read().splitlines() if ln.startswith("TOTAL")]
        result["coverage_gate"] = {"exit": grc, "total_line": total[-1] if total else "<none>", "log": str(out / "logs" / f"{name}_coverage_gate.log")}
    elif args.mode in ("new44", "file"):
        targets = new44 if args.mode == "new44" else [SEC]
        argv = base + LANE_SEL + targets + ["--timeout=60", "-v", "-rA", "--durations=0"]
        rc, summ, secs = _run(argv, wt, env, out / "logs" / f"{name}.log")
        result.update({"exit": rc, "summary": summ, "seconds": round(secs, 1), "log": str(out / "logs" / f"{name}.log")})
    else:
        argv = base + LANE_SEL + new44 + ["--timeout=60"]

        def one(i: int) -> dict:
            log = out / "logs" / name / f"run_{i:02d}.log"
            rc, summ, secs = _run(argv, wt, env, log)
            return {"run": i, "exit": rc, "summary": summ, "seconds": round(secs, 1)}

        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
            runs = list(pool.map(one, range(1, args.runs + 1)))
        result.update({
            "argv": argv, "runs": runs, "runs_total": len(runs),
            "runs_all_passed": sum(1 for r in runs if r["exit"] == 0),
            "distinct_summaries": sorted({re.sub(r" in [0-9.]+s.*$", "", r["summary"]) for r in runs}),
        })
        rc = 0 if result["runs_all_passed"] == len(runs) else 1
    dest = out / f"result_{name}.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("runs", "argv")}, indent=1))
    print(f"wrote {dest}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
