#!/usr/bin/env python3
"""
Run juniper-data's CI unit lane (or the whole suite, named files, or util/run_coverage.bash) on several trees at once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (counts for each cumulative stage tree against M0 and against its parent stage)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt; adapted from 2026-11-09_flood4r2_r17-data_run_lane.py

Usage:
    python3 <this> --python <venv interpreter> --out <dir> --mode lane|full|files|coverage-bash
                   --tree <name>=<juniper-data worktree> [--tree ...] [--workers N<=4] [--file <test file> ...]

MODES (each tree runs from its own root, so ``juniper_data`` is imported from that tree; a probe records the path)
    lane           ci.yml's ``unit-tests`` step as written at juniper-data 399eeffb:
                   ``python -m pytest -m "unit and not slow" juniper_data/tests/unit --verbose --timeout=60 --maxfail=5
                   --junitxml=... --cov=juniper_data --cov-report=term-missing --cov-report=xml:... --cov-report=html:...
                   --cov-report=json:...``, then ``python -m coverage report --fail-under=80``, then
                   ``juniper-coverage-gap-map --coverage-json <json> --enforce``. The only departures from CI: every
                   report path and COVERAGE_FILE point under --out, ``-p no:cacheprovider`` and
                   PYTHONDONTWRITEBYTECODE=1 are added, so the tree gains no file at all.
    full           ``python -B -m pytest -p no:cacheprovider juniper_data/tests/`` with a JUnit report.
    files          the lane's ``-m "unit and not slow"`` and ``--timeout=60`` over the named --file paths, ``-rA``.
    coverage-bash  ``bash util/run_coverage.bash`` with the venv's bin first on PATH (it writes the gitignored
                   ``reports/`` and ``.coverage`` into the tree; PYTEST_ADDOPTS adds ``-p no:cacheprovider``).

Each run writes <out>/<mode><tag>/<tree>/{run.log,junit.xml,...} and one <out>/<mode><tag>/result.json. TMPDIR is left
exactly as the session gave it. At most four trees run at once. From 2026-11-12 08:55Z every run also has the six
Sentry DSN variables set to "" (the consolidated plan's H-14: this host's shell exports one of them), and each
result names them; the runs before that inherited the session's environment unchanged.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: a chosen interpreter running pytest / coverage / the repo's own script
import sys
import time
import xml.etree.ElementTree as ET  # nosec B405 - parses JUnit files this script's own pytest runs just wrote
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LANE_SEL = ["-m", "unit and not slow"]
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
# pytest's last line, bordered or bare. It can also count warnings and "subtests passed", so only its start and its
# " in <seconds>s" are required.
SUMMARY_RE = re.compile(r"^=*\s*(\d+ (?:passed|failed|errors?|skipped|deselected)\b.*? in [0-9.]+s.*?)\s*=*$")


def _summary(text: str) -> str:
    hits = [m.group(1) for ln in text.splitlines() if (m := SUMMARY_RE.match(ln.strip()))]
    return hits[-1] if hits else "<no summary line>"


def _run(argv: list[str], cwd: Path, env: dict[str, str], log: Path, mode: str = "w") -> tuple[int, str, float]:
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with open(log, mode, encoding="utf-8") as fh:
        fh.write(f"$ (cwd={cwd}) {' '.join(argv)}\n")
        fh.flush()
        proc = subprocess.run(argv, cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT, check=False, timeout=3000)  # nosec B603
        elapsed = time.monotonic() - start
        fh.write(f"\n[exit {proc.returncode}] [{elapsed:.1f}s]\n")
    with open(log, encoding="utf-8") as fh:
        text = fh.read()
    return proc.returncode, text, elapsed


def _junit(path: Path) -> dict:
    counts = {"tests": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    per_file: dict[str, int] = {}
    if not path.is_file():
        return {"counts": counts, "per_file": per_file, "missing": True}
    for case in ET.parse(path).getroot().iter("testcase"):  # nosec B314
        tags = {child.tag for child in case}
        counts["tests"] += 1
        if "failure" in tags:
            counts["failed"] += 1
        elif "error" in tags:
            counts["errors"] += 1
        elif "skipped" in tags:
            counts["skipped"] += 1
        else:
            counts["passed"] += 1
        module = (case.get("classname") or "").split(".Test")[0]
        per_file[module] = per_file.get(module, 0) + 1
    return {"counts": counts, "per_file": per_file}


def _one(name: str, wt: Path, args: argparse.Namespace) -> dict:
    out = args.out.resolve() / f"{args.mode}{args.tag}" / name
    out.mkdir(parents=True, exist_ok=True)
    py = args.python
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **dict.fromkeys(SENTRY_DSN_NAMES, "")}
    probe = subprocess.run([py, "-B", "-c", "import juniper_data, sys; print(juniper_data.__file__); print(sys.version.split()[0])"], cwd=wt, env=env, capture_output=True, text=True, check=False)  # nosec B603
    where = probe.stdout.strip().splitlines()
    result: dict = {"tree": name, "worktree": str(wt), "mode": args.mode, "python": py, "python_version": where[1] if len(where) > 1 else None, "juniper_data_from": where[0] if where else None, "sentry_dsn_names_set_to_empty": list(SENTRY_DSN_NAMES)}
    result["imported_inside_tree"] = bool(where) and where[0].startswith(str(wt) + os.sep)
    log = out / "run.log"
    junit = out / "junit.xml"
    if args.mode == "lane":
        env["COVERAGE_FILE"] = str(out / ".coverage")
        argv = [py, "-m", "pytest", "-p", "no:cacheprovider", *LANE_SEL, "juniper_data/tests/unit", "--verbose", "--timeout=60", "--maxfail=5", f"--junitxml={junit}", "--cov=juniper_data", "--cov-report=term-missing", f"--cov-report=xml:{out / 'coverage.xml'}", f"--cov-report=html:{out / 'htmlcov'}", f"--cov-report=json:{out / 'coverage.json'}"]
        rc, text, secs = _run(argv, wt, env, log)
        result.update({"argv": argv, "exit": rc, "summary": _summary(text), "seconds": round(secs, 1), "log": str(log), "junit": _junit(junit)})
        grc, gtext = _run([py, "-m", "coverage", "report", "--fail-under=80"], wt, env, out / "coverage_gate.log")[:2]
        total = [ln for ln in gtext.splitlines() if ln.startswith("TOTAL")]
        result["aggregate_gate"] = {"exit": grc, "total_line": total[-1] if total else "<none>", "log": str(out / "coverage_gate.log")}
        if (out / "coverage.json").is_file():
            with open(out / "coverage.json", encoding="utf-8") as fh:
                totals = json.load(fh)["totals"]
            result["coverage_json_totals"] = {k: totals[k] for k in ("percent_covered", "percent_covered_display", "num_statements", "covered_lines", "num_branches", "covered_branches") if k in totals}
        gap = str(Path(py).parent / "juniper-coverage-gap-map")
        prc, ptext = _run([gap, "--coverage-json", str(out / "coverage.json"), "--enforce"], wt, env, out / "per_file_gate.log")[:2]
        verdict = [ln.strip() for ln in ptext.splitlines() if "Enforcing gate" in ln or ln.strip().startswith("Gated")]
        result["per_file_gate"] = {"exit": prc, "verdict_lines": verdict, "log": str(out / "per_file_gate.log")}
        result["ok"] = rc == 0 and grc == 0 and prc == 0
    elif args.mode == "full":
        argv = [py, "-B", "-m", "pytest", "-p", "no:cacheprovider", "juniper_data/tests/", f"--junitxml={junit}"]
        rc, text, secs = _run(argv, wt, env, log)
        result.update({"argv": argv, "exit": rc, "summary": _summary(text), "seconds": round(secs, 1), "log": str(log), "junit": _junit(junit), "ok": rc == 0})
    elif args.mode == "files":
        argv = [py, "-B", "-m", "pytest", "-p", "no:cacheprovider", *LANE_SEL, "--timeout=60", "-v", "-rA", f"--junitxml={junit}", *args.file]
        rc, text, secs = _run(argv, wt, env, log)
        result.update({"argv": argv, "exit": rc, "summary": _summary(text), "seconds": round(secs, 1), "log": str(log), "junit": _junit(junit), "ok": rc == 0})
    else:
        env["PATH"] = str(Path(py).parent) + os.pathsep + env.get("PATH", "")
        env["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
        argv = ["bash", "util/run_coverage.bash"]
        rc, text, secs = _run(argv, wt, env, log)
        keep = [ln.strip() for ln in text.splitlines() if ln.startswith(("TOTAL", "PASS:", "FAIL:", "WARN")) or "Enforcing gate" in ln or "Required test coverage" in ln]
        result.update({"argv": argv, "exit": rc, "summary": _summary(text), "seconds": round(secs, 1), "log": str(log), "lines": keep, "ok": rc == 0})
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--python", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", required=True, choices=["lane", "full", "files", "coverage-bash"])
    ap.add_argument("--tree", action="append", required=True, help="<name>=<worktree>")
    ap.add_argument("--file", action="append", default=[])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    trees = [item.split("=", 1) for item in args.tree]
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        results = list(pool.map(lambda pair: _one(pair[0], Path(pair[1]).resolve(), args), trees))
    dest = args.out.resolve() / f"{args.mode}{args.tag}" / "result.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
        fh.write("\n")
    for res in results:
        brief = {k: res.get(k) for k in ("tree", "exit", "summary", "seconds", "imported_inside_tree", "ok")}
        for key in ("aggregate_gate", "per_file_gate", "lines"):
            if key in res:
                brief[key] = res[key]
        if "junit" in res:
            brief["junit_counts"] = res["junit"]["counts"]
        print(json.dumps(brief))
    print(f"wrote {dest}")
    return 0 if all(r.get("ok") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
