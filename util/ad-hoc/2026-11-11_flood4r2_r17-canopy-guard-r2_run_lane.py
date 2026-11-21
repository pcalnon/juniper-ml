"""
Run canopy's CI unit lane (or a collection, or named files) in one tree behind the round-2 fence, and summarize it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round 2 of the Overtoad's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt)

Usage:
    python3 <this file> --tree <canopy tree> --python <interpreter> --label <name> --out <dir> --mode collect
    python3 <this file> --tree <canopy tree> --python <interpreter> --label <name> --out <dir> --mode lane [--cov]
    python3 <this file> --tree <canopy tree> --python <interpreter> --label <name> --out <dir> --mode files --paths <p>...

One pytest process, started as `<interpreter> 2026-11-11_flood4r2_r17-canopy-guard-r2_fenced_pytest.py <prefix> ...`
with cwd = the tree. `lane` is the unit step of .github/workflows/ci.yml: its selector, its four directories, its
three step variables, --verbose, --timeout=60 and --junitxml, in ONE process in CI's order. --maxfail=5 is left out
(with fewer than five failures it changes nothing, and an early stop would only hide results); --cov adds CI's
--cov=src with a JSON report and --cov-fail-under=80. `collect` adds --collect-only and writes the node ids.

The child environment is CI-like: every JUNIPER_/CASCOR_/CANOPY_ variable, LD_LIBRARY_PATH and PYTHONPATH are
dropped (CI's runner has none; only the count of dropped names is recorded) and LIBTORCH is emptied (this host's
shell carries another project's libtorch). TMPDIR is left as the session gave it.

pytest's --basetemp is <dir>/basetemp/<label>/bt, never under a canopy tree: on 2026-11-09 a validator's basetemp
under a canopy worktree's tmp/ vanished mid-run. A watcher thread polls that directory, its parents up to <dir>,
and a sentinel under the tree's tmp/, and writes <label>.vanish.jsonl (UTC time, path, the log's last lines) the
first time one disappears; the fence refuses and records an in-process shutil.rmtree of any of their ancestors.
Outputs in <dir>: <label>.log, .junit.xml, .census.jsonl, .rmtree.jsonl, .ids.txt (collect), .coverage.json (--cov)
and .summary.json.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import threading
import xml.etree.ElementTree as ET  # nosec B405 - our own pytest junit output
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FENCED = HERE / "2026-11-11_flood4r2_r17-canopy-guard-r2_fenced_pytest.py"
SELECTOR = "not requires_cascor and not requires_server and not slow"
DIRS = ["src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/"]
GUARDED = frozenset({*range(8050, 8060), 8200, 8201, 8202, 8210, 8211})


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def child_env(protect: list[Path]) -> tuple[dict[str, str], int]:
    env = dict(os.environ)
    dropped = [name for name in env if name.startswith(("JUNIPER_", "CASCOR_", "CANOPY_")) or name in ("LD_LIBRARY_PATH", "PYTHONPATH")]
    for name in dropped:
        env.pop(name)
    env.update(LIBTORCH="", CASCOR_BACKEND_AVAILABLE="0", RUN_SERVER_TESTS="0", ENABLE_SLOW_TESTS="0", PYTHONDONTWRITEBYTECODE="1", R2_PROTECT_DIRS=os.pathsep.join(str(path) for path in protect))
    return env, len(dropped)


def versions(python: str, env: dict[str, str]) -> str:
    code = "import sys, pytest, pytest_asyncio; print(sys.version.split()[0], 'pytest', pytest.__version__, 'pytest-asyncio', pytest_asyncio.__version__)"
    return subprocess.run([python, "-c", code], capture_output=True, text=True, env=env).stdout.strip()  # nosec B603 - fixed argv


def junit_summary(path: Path) -> dict:
    if not path.exists():
        return {"missing": True}
    root = ET.parse(path).getroot()  # nosec B314 - our own pytest junit output
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    failed = []
    for case in suite.iter("testcase"):
        for kind in ("failure", "error"):
            node = case.find(kind)
            if node is not None:
                failed.append({"id": f"{case.get('classname')}::{case.get('name')}", "kind": kind, "message": (node.get("message") or "").splitlines()[0][:300] if node.get("message") else ""})
    return {key: suite.get(key) for key in ("tests", "failures", "errors", "skipped", "time")} | {"failed": failed}


def census_summary(path: Path) -> dict:
    by_port: dict[int, dict] = defaultdict(lambda: {"connects": 0, "refused": 0, "tests": set(), "files": set(), "phases": Counter(), "threads": Counter()})
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            slot = by_port[rec["port"]]
            slot["connects"] += 1
            slot["refused"] += int(rec["refused"])
            slot["tests"].add(rec["nodeid"] or "<none>")
            slot["files"].add((rec["nodeid"] or "<none>").split("::", 1)[0])
            slot["phases"][rec["phase"]] += 1
            slot["threads"]["MainThread" if rec["thread"] == "MainThread" else "other"] += 1
    result = {}
    for port, slot in sorted(by_port.items()):
        result[str(port)] = {"connects": slot["connects"], "refused_by_fence": slot["refused"], "distinct_tests": len(slot["tests"]), "distinct_files": len(slot["files"]), "phases": dict(slot["phases"]), "threads": dict(slot["threads"]), "guarded_port": port in GUARDED}
        if port in GUARDED:
            result[str(port)]["tests"] = sorted(slot["tests"])
    return result


class Watcher:
    """Records the first time each watched directory, once seen, stops existing."""

    def __init__(self, watched: list[Path], log: Path, out: Path) -> None:
        self.watched = watched
        self.log = log
        self.out = out
        self.seen: set[Path] = set()
        self.gone: set[Path] = set()
        self.stop = threading.Event()
        self.events: list[dict] = []
        self.thread = threading.Thread(target=self.run, daemon=True, name="r2-vanish-watcher")

    def poll(self) -> None:
        for path in self.watched:
            if path.exists():
                self.seen.add(path)
            elif path in self.seen and path not in self.gone:
                self.gone.add(path)
                tail = self.log.read_text(encoding="utf-8", errors="replace").splitlines()[-3:] if self.log.exists() else []
                event = {"utc": utc_now(), "vanished": str(path), "log_tail": tail}
                self.events.append(event)
                with self.out.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event) + "\n")

    def run(self) -> None:
        while not self.stop.wait(1.0):
            self.poll()
        self.poll()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run canopy's CI unit lane, a collection or named files behind the round-2 fence.")
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("collect", "lane", "files"))
    parser.add_argument("--paths", nargs="*", default=[])
    parser.add_argument("--cov", action="store_true")
    parser.add_argument("--extra", nargs="*", default=[], help="further pytest arguments, appended last")
    args = parser.parse_args()
    tree, out = args.tree.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    basetemp = out / "basetemp" / args.label / "bt"
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    sentinel = tree / "tmp" / f"r2-sentinel-{args.label}"
    sentinel.mkdir(parents=True, exist_ok=True)
    prefix = out / args.label
    log_path, junit_path = Path(f"{prefix}.log"), Path(f"{prefix}.junit.xml")
    env, dropped = child_env([basetemp, sentinel, out / "r2-protected"])  # the third names no file: it makes an rmtree of <dir> or above a refusal

    targets = args.paths if args.mode == "files" else DIRS
    if args.mode == "files" and not targets:
        raise SystemExit("--mode files needs --paths (an empty list would fall back to testpaths, the whole suite)")
    pytest_args = ["-m", SELECTOR, *targets, "-p", "no:cacheprovider", f"--basetemp={basetemp}"]
    if args.mode == "collect":
        pytest_args += ["--collect-only"]  # canopy's addopts carry -q, which prints one node id per line
    else:
        pytest_args += ["--verbose", "--timeout=60", f"--junitxml={junit_path}"]
        if args.cov:
            pytest_args += ["--cov=src", f"--cov-report=json:{prefix}.coverage.json", "--cov-fail-under=80"]
    pytest_args += args.extra
    argv = [args.python, str(FENCED), str(prefix), *pytest_args]

    watcher = Watcher([out, basetemp.parent, basetemp, sentinel], log_path, Path(f"{prefix}.vanish.jsonl"))
    started = utc_now()
    watcher.thread.start()
    with log_path.open("w", encoding="utf-8") as log:
        code = subprocess.run(argv, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT).returncode  # nosec B603 - fixed argv
    watcher.stop.set()
    watcher.thread.join(timeout=10)

    text = log_path.read_text(encoding="utf-8", errors="replace")
    summary = {"label": args.label, "mode": args.mode, "tree": str(tree), "interpreter": args.python, "versions": versions(args.python, env), "argv": argv, "cwd": str(tree), "env_note": f"dropped {dropped} variables (JUNIPER_/CASCOR_/CANOPY_ prefixes, LD_LIBRARY_PATH, PYTHONPATH; names not recorded); LIBTORCH emptied; CI's three step variables set", "started_utc": started, "ended_utc": utc_now(), "exit": code, "vanish_events": watcher.events, "last_lines": text.splitlines()[-4:]}
    if args.mode == "collect":
        ids = [line.strip() for line in text.splitlines() if "::" in line and not line.startswith(" ") and line.startswith("src/")]
        Path(f"{prefix}.ids.txt").write_text("\n".join(ids) + "\n", encoding="utf-8")
        summary["collected_ids"] = len(ids)
        summary["collect_line"] = [line for line in text.splitlines() if "collected" in line or "deselected" in line][-1:]
    else:
        summary["junit"] = junit_summary(junit_path)
        summary["census"] = census_summary(Path(f"{prefix}.census.jsonl"))
        summary["guarded_port_connects_past_the_guard"] = sum(slot["connects"] for slot in summary["census"].values() if slot["guarded_port"])
    rmtree_log = Path(f"{prefix}.rmtree.jsonl")
    summary["rmtree_refusals"] = len(rmtree_log.read_text(encoding="utf-8").splitlines()) if rmtree_log.exists() else None
    Path(f"{prefix}.summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    brief = {key: summary[key] for key in ("label", "versions", "exit", "started_utc", "ended_utc", "vanish_events", "rmtree_refusals") if key in summary}
    brief |= {key: summary[key] for key in ("collected_ids", "collect_line", "guarded_port_connects_past_the_guard") if key in summary}
    if "junit" in summary:
        brief["junit"] = summary["junit"]
        brief["census_ports"] = {port: {key: slot[key] for key in ("connects", "distinct_tests", "distinct_files")} for port, slot in summary["census"].items()}
    print(json.dumps(brief, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
