"""
Run juniper-canopy's CI unit lane (or named tests) in one tree behind the r27 connect fence, and summarize it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8),
    juniper-canopy unit-lane :8100 connects; adapted from util/ad-hoc/2026-11-11_flood4r2_r17-canopy-guard-r2_run_lane.py

Usage:
    python3 <this file> --tree <canopy tree> --python <interpreter> --label <name> --out <dir> --mode lane [--cov] [--maxfail N]
    python3 <this file> --tree <canopy tree> --python <interpreter> --label <name> --out <dir> --mode files --paths <p>...
    python3 <this file> --tree <canopy tree> --python <interpreter> --label <name> --out <dir> --mode collect

One pytest process, `<interpreter> 2026-11-25_flood4_s14_r27_fenced_pytest.py <prefix> ...` with cwd = the tree.
`lane` is the unit step of the tree's .github/workflows/ci.yml ("Run Unit Tests with Coverage Gate"): its -m selector,
its four directories, its three step variables, --verbose, --timeout=60 and --junitxml; --cov adds CI's --cov=src with
its term-missing, xml, json and html reports (written under <dir>) and --cov-fail-under=80; --maxfail N adds CI's
--maxfail. `files` runs the named paths or node ids with the same options. `collect` adds --collect-only -q.

The child environment is CI-like: every JUNIPER_/CASCOR_/CANOPY_ variable, LD_LIBRARY_PATH and PYTHONPATH are dropped
(only their count is recorded) except the four Sentry variables of that form, which stay set to "" as the session's
run wrapper sets them (SENTRY_DSN and SENTRY_SDK_DSN stay ""); LIBTORCH is emptied; PYTHONDONTWRITEBYTECODE=1. TMPDIR
is left as the session gave it; pytest's --basetemp is <dir>/basetemp/<label>, outside the tree.

Outputs in <dir>: <label>.log, .junit.xml, .census.jsonl, .guard.jsonl, .listening_at_start.json, .ids.txt (collect),
.coverage.json/.coverage.xml/htmlcov-<label>/ (--cov) and .summary.json, which holds the junit counts, the failed
tests, the census per port (connects, distinct tests and files, tests by phase, the opening code, per file) and the
guard's failed reports.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import xml.etree.ElementTree as ET  # nosec B405 - our own pytest junit output
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FENCED = HERE / "2026-11-25_flood4_s14_r27_fenced_pytest.py"
SELECTOR = "not requires_cascor and not requires_server and not slow"
DIRS = ["src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/"]
GUARDED_AFTER = frozenset({*range(8050, 8060), 8100, 8200, 8201, 8202, 8210, 8211})
KEEP_EMPTY = ("JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def child_env() -> tuple[dict[str, str], int]:
    env = dict(os.environ)
    dropped = [name for name in env if (name.startswith(("JUNIPER_", "CASCOR_", "CANOPY_")) and name not in KEEP_EMPTY) or name in ("LD_LIBRARY_PATH", "PYTHONPATH")]
    for name in dropped:
        env.pop(name)
    env.update({name: "" for name in KEEP_EMPTY})
    env.update(SENTRY_DSN="", SENTRY_SDK_DSN="", LIBTORCH="", CASCOR_BACKEND_AVAILABLE="0", RUN_SERVER_TESTS="0", ENABLE_SLOW_TESTS="0", PYTHONDONTWRITEBYTECODE="1")
    return env, len(dropped)


def versions(python: str, env: dict[str, str]) -> str:
    code = "import sys, pytest, pytest_asyncio; print(sys.version.split()[0], sys.executable, sys.base_prefix, 'pytest', pytest.__version__, 'pytest-asyncio', pytest_asyncio.__version__)"
    return subprocess.run([python, "-c", code], capture_output=True, text=True, env=env, check=False).stdout.strip()  # nosec B603 - fixed argv


def junit_summary(path: Path) -> dict:
    if not path.exists():
        return {"missing": True}
    root = ET.parse(path).getroot()  # nosec B314 - our own pytest junit output
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    failed, cases = [], 0
    for case in suite.iter("testcase"):
        cases += 1
        for kind in ("failure", "error"):
            node = case.find(kind)
            if node is not None:
                message = (node.get("message") or "").splitlines()
                failed.append({"id": f"{case.get('classname')}::{case.get('name')}", "kind": kind, "message": message[0][:300] if message else ""})
    return {key: suite.get(key) for key in ("tests", "failures", "errors", "skipped", "time")} | {"testcase_elements": cases, "failed": failed}


def _opener(record: dict) -> str:
    """The canopy code that opened a connect: its own stack, else the stack of the httpx request it serves."""
    frames = record.get("src_frames") or record.get("request_src_frames") or []
    if not frames:
        tests = [frame for frame in (record.get("test_frames") or []) + (record.get("request_test_frames") or []) if "_guarded_connect" not in frame]
        return "<no canopy src frame>" + (f" (test {tests[0]})" if tests else "")
    return " <- ".join(frames[:3])


def census_summary(path: Path) -> dict:
    by_port: dict[int, dict] = defaultdict(lambda: {"connects": 0, "refused_by_fence": 0, "hosts": Counter(), "requests": Counter(), "tests": set(), "files": Counter(), "tests_by_phase": defaultdict(set), "threads": Counter(), "openers": defaultdict(lambda: {"connects": 0, "tests": set()}), "per_test": defaultdict(Counter)})
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            slot = by_port[rec["port"]]
            nodeid = rec["nodeid"] or "<none>"
            slot["connects"] += 1
            slot["refused_by_fence"] += int(rec["refused"])
            slot["hosts"][rec["host"]] += 1
            slot["requests"][rec.get("request") or "<not an httpx async request>"] += 1
            slot["tests"].add(nodeid)
            slot["tests_by_phase"][rec["phase"]].add(nodeid)
            slot["threads"]["MainThread" if rec["thread"] == "MainThread" else "other"] += 1
            opener = slot["openers"][_opener(rec)]
            opener["connects"] += 1
            opener["tests"].add(nodeid)
            slot["per_test"][nodeid][rec["phase"]] += 1
    result = {}
    for port, slot in sorted(by_port.items()):
        files = Counter(nodeid.split("::", 1)[0] for nodeid in slot["tests"])
        phases = {phase: len(tests) for phase, tests in sorted(slot["tests_by_phase"].items())}
        setup, call = slot["tests_by_phase"].get("setup", set()), slot["tests_by_phase"].get("call", set())
        result[str(port)] = {
            "connects": slot["connects"],
            "refused_by_fence": slot["refused_by_fence"],
            "hosts": dict(slot["hosts"]),
            "requests": dict(slot["requests"].most_common()),
            "distinct_tests": len(slot["tests"]),
            "distinct_files": len(files),
            "distinct_tests_by_phase": phases,
            "tests_in_setup_and_call": len(setup & call),
            "threads": dict(slot["threads"]),
            "openers": {key: {"connects": value["connects"], "distinct_tests": len(value["tests"])} for key, value in sorted(slot["openers"].items(), key=lambda kv: -kv[1]["connects"])},
            "files_by_test_count": dict(sorted(files.items(), key=lambda kv: (-kv[1], kv[0]))),
            "guarded_after_r27": port in GUARDED_AFTER,
            "per_test": {nodeid: dict(counter) for nodeid, counter in sorted(slot["per_test"].items())},
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run canopy's CI unit lane or named tests behind the r27 connect fence.")
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("collect", "lane", "files"))
    parser.add_argument("--paths", nargs="*", default=[])
    parser.add_argument("--cov", action="store_true")
    parser.add_argument("--maxfail", type=int, default=None)
    parser.add_argument("--no-selector", action="store_true", help="files mode: run the named ids without CI's -m selector")
    parser.add_argument("--extra", nargs="*", default=[], help="further pytest arguments, appended last")
    args = parser.parse_args()
    tree, out = args.tree.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    basetemp = out / "basetemp" / args.label
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    prefix = out / args.label
    log_path, junit_path = Path(f"{prefix}.log"), Path(f"{prefix}.junit.xml")
    env, dropped = child_env()

    targets = args.paths if args.mode == "files" else DIRS
    if args.mode == "files" and not targets:
        raise SystemExit("--mode files needs --paths (an empty list would fall back to testpaths, the whole suite)")
    pytest_args = ([] if args.no_selector else ["-m", SELECTOR]) + [*targets, "-p", "no:cacheprovider", f"--basetemp={basetemp}"]
    if args.mode == "collect":
        pytest_args += ["--collect-only"]
    else:
        pytest_args += ["--verbose", "--timeout=60"]
        if args.maxfail is not None:
            pytest_args += [f"--maxfail={args.maxfail}"]
        pytest_args += [f"--junitxml={junit_path}"]
        if args.cov:
            pytest_args += ["--cov=src", "--cov-report=term-missing", f"--cov-report=xml:{prefix}.coverage.xml", f"--cov-report=json:{prefix}.coverage.json", f"--cov-report=html:{out / ('htmlcov-' + args.label)}", "--cov-fail-under=80"]
    pytest_args += args.extra
    argv = [args.python, str(FENCED), str(prefix), *pytest_args]

    started = utc_now()
    with log_path.open("w", encoding="utf-8") as log:
        code = subprocess.run(argv, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, check=False).returncode  # nosec B603 - fixed argv
    text = log_path.read_text(encoding="utf-8", errors="replace")
    summary = {"label": args.label, "mode": args.mode, "tree": str(tree), "interpreter": args.python, "versions": versions(args.python, env), "argv": argv, "cwd": str(tree), "env_note": f"dropped {dropped} variables (JUNIPER_/CASCOR_/CANOPY_ prefixes except the four Sentry DSNs, kept empty; LD_LIBRARY_PATH; PYTHONPATH; names not recorded); LIBTORCH emptied; CI's three step variables set", "started_utc": started, "ended_utc": utc_now(), "exit": code, "last_lines": text.splitlines()[-4:]}
    if args.mode == "collect":
        ids = [line.strip() for line in text.splitlines() if "::" in line and line.startswith("src/")]
        Path(f"{prefix}.ids.txt").write_text("\n".join(ids) + "\n", encoding="utf-8")
        summary["collected_ids"] = len(ids)
        summary["collect_line"] = [line for line in text.splitlines() if "collected" in line or "deselected" in line][-1:]
    else:
        summary["junit"] = junit_summary(junit_path)
        summary["census"] = census_summary(Path(f"{prefix}.census.jsonl"))
        guard_path = Path(f"{prefix}.guard.jsonl")
        guard = [json.loads(line) for line in guard_path.read_text(encoding="utf-8").splitlines()] if guard_path.exists() else []
        summary["guard_failed_reports"] = guard
        summary["connects_to_guarded_ports_at_socket_level"] = sum(slot["connects"] for slot in summary["census"].values() if slot["guarded_after_r27"])
        summary["result_line"] = [line for line in text.splitlines() if (" passed" in line or " failed" in line) and line.startswith("=")][-1:]
    Path(f"{prefix}.summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    brief = {key: summary[key] for key in ("label", "versions", "exit", "started_utc", "ended_utc", "collected_ids", "collect_line", "result_line", "connects_to_guarded_ports_at_socket_level") if key in summary}
    if "junit" in summary:
        brief["junit"] = {key: value for key, value in summary["junit"].items() if key != "failed"} | {"failed": [entry["id"] for entry in summary["junit"].get("failed", [])][:40]}
        brief["census_ports"] = {port: {key: slot[key] for key in ("connects", "distinct_tests", "distinct_files", "distinct_tests_by_phase")} for port, slot in summary["census"].items()}
        brief["guard_failed_reports"] = len(summary["guard_failed_reports"])
    print(json.dumps(brief, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
