#!/usr/bin/env python3
"""
Run juniper-data's CI unit lane, its integration lane, a named node list, or a node list N times, on up to four trees.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (lane counts and runtimes before and after the marks; the newly selected tests alone, repeated)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#529 (the precedent);
         adapted from 2026-11-11_flood4r2_data-landing_run_lane.py

Usage:
    python3 <this> --mode unit-lane|integration-lane|nodes|repeat --out <dir> --tag <name>
                   --job <name>=<venv interpreter>=<juniper-data tree> [--job ...] [--workers N<=4]
                   [--nodes <file with one node id or path per line>] [--times N] [--marker <-m expression>]
                   [--pytest-arg=<one more pytest option> ...]

MODES (each job runs from its tree's root, so ``juniper_data`` is imported from that tree; a probe records the path)
    unit-lane         ci.yml's ``unit-tests`` step as written at juniper-data c68e6b4c:
                      ``python -m pytest -m "unit and not slow" juniper_data/tests/unit --verbose --timeout=60 --maxfail=5
                      --junitxml=... --cov=juniper_data --cov-report=term-missing --cov-report=xml:... --cov-report=html:...
                      --cov-report=json:...``, then ``python -m coverage report --fail-under=80``, then
                      ``juniper-coverage-gap-map --coverage-json <json> --enforce``.
    integration-lane  ci.yml's ``integration-tests`` step: ``python -m pytest -m "integration and not slow"
                      juniper_data/tests/integration --verbose --timeout=120 --maxfail=3 --junitxml=...``.
    nodes             ``python -m pytest -rA --junitxml=... <the node ids>``, with ``-m <expression>`` when --marker is given.
    repeat            the ``nodes`` run --times times per job, each a fresh process, at most --workers at once.

The only departures from CI: every report path and COVERAGE_FILE point under --out, and ``-p no:cacheprovider`` and
PYTHONDONTWRITEBYTECODE=1 are added, so the tree gains no report and no bytecode. TMPDIR is left exactly as the session
gave it. Every run has the six Sentry DSN variables set to "" and three token variables removed from its environment
(a hosted runner has neither). At most four processes run at once.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: a chosen interpreter running pytest / coverage / the per-file gate
import sys
import time
import xml.etree.ElementTree as ET  # nosec B405 - parses JUnit files this script's own pytest runs just wrote
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
DROPPED_TOKEN_NAMES = ("HF_TOKEN", "JUNIPER_ML_PYPI", "JUNIPER_ML_TEST_PYPI")
SUMMARY_RE = re.compile(r"^=*\s*(\d+ (?:passed|failed|errors?|skipped|deselected)\b.*? in [0-9.]+s.*?)\s*=*$")


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in DROPPED_TOKEN_NAMES}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", **dict.fromkeys(SENTRY_DSN_NAMES, "")})
    env.update(extra or {})
    return env


def _summary(text: str) -> str:
    hits = [m.group(1) for ln in text.splitlines() if (m := SUMMARY_RE.match(ln.strip()))]
    return hits[-1] if hits else "<no summary line>"


def _run(argv: list[str], cwd: Path, env: dict[str, str], log: Path) -> tuple[int, str, float]:
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(f"$ (cwd={cwd}) {' '.join(argv)}\n")
        fh.flush()
        proc = subprocess.run(argv, cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT, check=False, timeout=3300)  # nosec B603
        elapsed = time.monotonic() - start
        fh.write(f"\n[exit {proc.returncode}] [{elapsed:.1f}s]\n")
    with open(log, encoding="utf-8") as fh:
        text = fh.read()
    return proc.returncode, text, elapsed


def _junit(path: Path) -> dict:
    counts = {"tests": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    per_file: dict[str, dict] = {}
    not_passed: list[dict] = []
    seconds = 0.0
    if not path.is_file():
        return {"counts": counts, "per_file": per_file, "missing": True}
    for case in ET.parse(path).getroot().iter("testcase"):  # nosec B314
        tags = {child.tag for child in case}
        outcome = "failed" if "failure" in tags else "errors" if "error" in tags else "skipped" if "skipped" in tags else "passed"
        counts["tests"] += 1
        counts[outcome] += 1
        duration = float(case.get("time") or 0.0)
        seconds += duration
        module = (case.get("classname") or "").rsplit(".Test", 1)[0]
        entry = per_file.setdefault(module, {"tests": 0, "seconds": 0.0})
        entry["tests"] += 1
        entry["seconds"] = round(entry["seconds"] + duration, 3)
        if outcome != "passed":
            not_passed.append({"id": f"{case.get('classname')}::{case.get('name')}", "outcome": outcome})
    return {"counts": counts, "testcase_seconds": round(seconds, 2), "per_file": per_file, "not_passed": not_passed}


def _probe(py: str, wt: Path) -> dict:
    proc = subprocess.run([py, "-B", "-c", "import juniper_data, sys; print(juniper_data.__file__); print(sys.version.split()[0])"], cwd=wt, env=_env(), capture_output=True, text=True, check=False)  # nosec B603
    where = proc.stdout.strip().splitlines()
    return {"python": py, "python_version": where[1] if len(where) > 1 else None, "juniper_data_from": where[0] if where else None, "imported_inside_tree": bool(where) and where[0].startswith(str(wt) + os.sep)}


def _unit_lane(name: str, py: str, wt: Path, out: Path) -> dict:
    result = {"job": name, "worktree": str(wt), **_probe(py, wt)}
    junit = out / "junit-unit.xml"
    env = _env({"COVERAGE_FILE": str(out / ".coverage")})
    argv = [py, "-m", "pytest", "-p", "no:cacheprovider", "-m", "unit and not slow", "juniper_data/tests/unit", "--verbose", "--timeout=60", "--maxfail=5", f"--junitxml={junit}", "--cov=juniper_data", "--cov-report=term-missing", f"--cov-report=xml:{out / 'coverage.xml'}", f"--cov-report=html:{out / 'htmlcov'}", f"--cov-report=json:{out / 'coverage.json'}"]
    rc, text, secs = _run(argv, wt, env, out / "run.log")
    result.update({"argv": argv, "exit": rc, "summary": _summary(text), "seconds": round(secs, 1), "log": str(out / "run.log"), "junit": _junit(junit)})
    grc, gtext = _run([py, "-m", "coverage", "report", "--fail-under=80"], wt, env, out / "coverage_gate.log")[:2]
    total = [ln for ln in gtext.splitlines() if ln.startswith("TOTAL")]
    result["aggregate_gate"] = {"exit": grc, "total_line": total[-1] if total else "<none>", "log": str(out / "coverage_gate.log")}
    if (out / "coverage.json").is_file():
        with open(out / "coverage.json", encoding="utf-8") as fh:
            cov = json.load(fh)
        result["coverage_json_totals"] = {k: cov["totals"][k] for k in ("percent_covered", "num_statements", "covered_lines", "missing_lines", "num_branches", "covered_branches") if k in cov["totals"]}
        result["coverage_per_file"] = {path: {"statements": f["summary"]["num_statements"], "missing": f["summary"]["missing_lines"], "missing_lines": f["missing_lines"]} for path, f in sorted(cov["files"].items())}
    gap = str(Path(py).parent / "juniper-coverage-gap-map")
    prc, ptext = _run([gap, "--coverage-json", str(out / "coverage.json"), "--enforce"], wt, env, out / "per_file_gate.log")[:2]
    verdict = [ln.strip() for ln in ptext.splitlines() if "Enforcing gate" in ln or ln.strip().startswith(("Gated", "PASS", "FAIL"))]
    result["per_file_gate"] = {"exit": prc, "verdict_lines": verdict, "log": str(out / "per_file_gate.log")}
    result["ok"] = rc == 0 and grc == 0 and prc == 0
    return result


def _integration_lane(name: str, py: str, wt: Path, out: Path) -> dict:
    junit = out / "junit-integration.xml"
    argv = [py, "-m", "pytest", "-p", "no:cacheprovider", "-m", "integration and not slow", "juniper_data/tests/integration", "--verbose", "--timeout=120", "--maxfail=3", f"--junitxml={junit}"]
    rc, text, secs = _run(argv, wt, _env(), out / "run.log")
    return {"job": name, "worktree": str(wt), **_probe(py, wt), "argv": argv, "exit": rc, "summary": _summary(text), "seconds": round(secs, 1), "log": str(out / "run.log"), "junit": _junit(junit), "ok": rc == 0}


def _nodes(name: str, py: str, wt: Path, out: Path, nodes: list[str], marker: str | None, extra: list[str], stem: str = "run") -> dict:
    junit = out / f"{stem}.xml"
    select = [*(["-m", marker] if marker else []), *extra]
    argv = [py, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-rA", f"--junitxml={junit}", *select, *nodes]
    rc, text, secs = _run(argv, wt, _env(), out / f"{stem}.log")
    shown = argv if len(nodes) <= 12 else [*argv[: len(argv) - len(nodes)], f"<{len(nodes)} node ids from --nodes>"]
    return {"job": name, "worktree": str(wt), "argv": shown, "exit": rc, "summary": _summary(text), "seconds": round(secs, 1), "log": str(out / f"{stem}.log"), "junit": _junit(junit), "ok": rc == 0}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--mode", required=True, choices=["unit-lane", "integration-lane", "nodes", "repeat"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--job", action="append", required=True, help="<name>=<venv interpreter>=<juniper-data tree>")
    ap.add_argument("--nodes", type=Path)
    ap.add_argument("--marker")
    ap.add_argument("--pytest-arg", action="append", default=[], help="one more pytest option for the nodes / repeat modes, e.g. --pytest-arg=--benchmark-enable")
    ap.add_argument("--times", type=int, default=20)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    jobs = [item.split("=", 2) for item in args.job]
    base = args.out.resolve() / f"{args.mode}_{args.tag}"
    workers = max(1, min(args.workers, 4))
    nodes: list[str] = []
    if args.nodes:
        with open(args.nodes, encoding="utf-8") as fh:
            nodes = [ln.strip() for ln in fh if ln.strip()]
    if args.mode in ("nodes", "repeat") and not nodes:
        ap.error("--nodes is required for this mode and must name at least one node")

    def one(job: list[str]) -> dict:
        name, py, tree = job
        wt = Path(tree).resolve()
        out = base / name
        out.mkdir(parents=True, exist_ok=True)
        if args.mode == "unit-lane":
            return _unit_lane(name, py, wt, out)
        if args.mode == "integration-lane":
            return _integration_lane(name, py, wt, out)
        return {**_probe(py, wt), **_nodes(name, py, wt, out, nodes, args.marker, args.pytest_arg)}

    if args.mode == "repeat":
        work = [(job, n) for job in jobs for n in range(1, args.times + 1)]

        def rep(item: tuple[list[str], int]) -> dict:
            (name, py, tree), n = item
            out = base / name
            out.mkdir(parents=True, exist_ok=True)
            res = _nodes(name, py, Path(tree).resolve(), out, nodes, args.marker, args.pytest_arg, stem=f"run{n:02d}")
            return {"job": name, "run": n, "exit": res["exit"], "summary": res["summary"], "seconds": res["seconds"], "counts": res["junit"]["counts"], "not_passed": res["junit"].get("not_passed", [])}

        with ThreadPoolExecutor(max_workers=workers) as pool:
            runs = list(pool.map(rep, work))
        results: list[dict] = []
        for name, py, tree in jobs:
            mine = [r for r in runs if r["job"] == name]
            flaky: dict[str, int] = {}
            for r in mine:
                for bad in r["not_passed"]:
                    if bad["outcome"] != "skipped":
                        flaky[bad["id"]] = flaky.get(bad["id"], 0) + 1
            results.append({**_probe(py, Path(tree).resolve()), "job": name, "worktree": tree, "nodes": len(nodes), "times": args.times, "workers": workers, "runs_exit_0": sum(1 for r in mine if r["exit"] == 0), "summaries": sorted({re.sub(r" in [0-9.]+s.*", "", r["summary"]) for r in mine}), "seconds_min_max": [min(r["seconds"] for r in mine), max(r["seconds"] for r in mine)], "failed_or_errored_by_test": flaky, "ok": all(r["exit"] == 0 for r in mine), "runs": mine})
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(one, jobs))
    base.mkdir(parents=True, exist_ok=True)
    dest = base / "result.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump({"mode": args.mode, "tag": args.tag, "sentry_dsn_names_set_to_empty": list(SENTRY_DSN_NAMES), "token_names_removed": list(DROPPED_TOKEN_NAMES), "results": results}, fh, indent=1)
        fh.write("\n")
    for res in results:
        brief = {k: res.get(k) for k in ("job", "python_version", "imported_inside_tree", "exit", "summary", "seconds", "ok", "runs_exit_0", "times", "summaries", "seconds_min_max", "failed_or_errored_by_test") if k in res}
        for key in ("aggregate_gate", "per_file_gate", "coverage_json_totals"):
            if key in res:
                brief[key] = res[key]
        if "junit" in res:
            brief["junit_counts"] = res["junit"]["counts"]
            brief["junit_testcase_seconds"] = res["junit"].get("testcase_seconds")
            brief["not_passed"] = [b for b in res["junit"].get("not_passed", []) if b["outcome"] != "skipped"][:40]
        print(json.dumps(brief))
    print(f"wrote {dest}")
    return 0 if all(r.get("ok") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
