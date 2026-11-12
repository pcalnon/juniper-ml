"""
Run canopy's CI unit lane in four concurrent file-balanced groups under the census runner, then summarize.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 round-2 validation of the owner's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/BRIEF_VALIDATE_R2.txt)

Usage:
    python3 util/ad-hoc/2026-11-09_flood4r2_val_r17-canopy-guard_run_groups.py <worktree> <label> [--collect-only] [--groups=N]

Uses CI's unit-step selector, directories and step env (CASCOR_BACKEND_AVAILABLE=0, RUN_SERVER_TESTS=0,
ENABLE_SLOW_TESTS=0); the child env drops LD_LIBRARY_PATH, empties LIBTORCH (this host's shell carries a Rust
project's libtorch) and drops every JUNIPER_/CASCOR_/CANOPY_ variable (CI's runner has none), recording only how
many were dropped. Files are split across four groups by test count (no file is split), each group runs in its own
process with its own --basetemp under the worktree's tmp/, and junit + census JSONL land in the validator's
scratch dir under runs/<label>/. --collect-only writes the selected node ids and the summary line and stops.
"""

from __future__ import annotations

import json
import os
import re
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import xml.etree.ElementTree as ET  # nosec B405 - our own pytest junit output
from collections import Counter, defaultdict
from pathlib import Path

PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
ORCH = Path(__file__).resolve().parents[2]
SCRATCH = ORCH / "tmp" / "flood4r2-val" / "r17-canopy-network-guard"
RUNNER = Path(__file__).resolve().parent / "2026-11-09_flood4r2_val_r17-canopy-guard_census_runner.py"
SELECTOR = "not requires_cascor and not requires_server and not slow"
DIRS = ["src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/"]
GROUPS = int(next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--groups=")), "4"))


def child_env() -> tuple[dict[str, str], int]:
    env = dict(os.environ)
    dropped = [name for name in env if name.startswith(("JUNIPER_", "CASCOR_", "CANOPY_"))]
    for name in dropped:
        env.pop(name)
    env.pop("LD_LIBRARY_PATH", None)
    env["LIBTORCH"] = ""
    env.update(CASCOR_BACKEND_AVAILABLE="0", RUN_SERVER_TESTS="0", ENABLE_SLOW_TESTS="0", PYTHONDONTWRITEBYTECODE="1")
    return env, len(dropped)


def collect(worktree: Path, env: dict[str, str], out: Path) -> list[str]:
    # canopy's addopts already carry -q, which prints node ids; another -q would print "file: N" lines instead.
    proc = subprocess.run([PY, "-m", "pytest", "--collect-only", "-p", "no:cacheprovider", "-m", SELECTOR, *DIRS], cwd=worktree, env=env, capture_output=True, text=True)  # nosec B603
    ids = [line.strip() for line in proc.stdout.splitlines() if "::" in line and not line.startswith(" ")]
    summary = [line for line in proc.stdout.splitlines() if "collected" in line or "deselected" in line or "error" in line.lower()]
    (out / "collect_ids.txt").write_text("\n".join(ids) + "\n", encoding="utf-8")
    (out / "collect_summary.txt").write_text(f"exit {proc.returncode}\n" + "\n".join(summary[-5:]) + "\n" + proc.stderr[-3000:], encoding="utf-8")
    print(f"collect exit {proc.returncode}; ids {len(ids)}; summary {summary[-1:] if summary else None}")
    return ids


def split(ids: list[str]) -> list[list[str]]:
    per_file = Counter(node.split("::", 1)[0] for node in ids)
    groups: list[list[str]] = [[] for _ in range(GROUPS)]
    load = [0] * GROUPS
    for path, count in sorted(per_file.items(), key=lambda kv: (-kv[1], kv[0])):
        index = load.index(min(load))
        groups[index].append(path)
        load[index] += count
    print(f"group loads: {load}")
    return [sorted(group) for group in groups]


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
                message = (node.get("message") or "").splitlines()[0][:300] if node.get("message") else ""
                failed.append({"id": f"{case.get('classname')}::{case.get('name')}", "kind": kind, "message": message})
    return {key: suite.get(key) for key in ("tests", "failures", "errors", "skipped", "time")} | {"failed": failed}


def census_summary(paths: list[Path]) -> dict:
    by_port: dict[int, dict] = defaultdict(lambda: {"connects": 0, "tests": set(), "phases": Counter(), "threads": Counter(), "files": Counter(), "src_frames": Counter(), "refused": 0})
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            slot = by_port[rec["port"]]
            slot["connects"] += 1
            slot["refused"] += int(rec["refused"])
            slot["tests"].add(rec["nodeid"])
            slot["phases"][rec["phase"]] += 1
            slot["threads"]["MainThread" if rec["thread"] == "MainThread" else "other:" + re.sub(r"\d+", "N", rec["thread"])] += 1
            slot["files"][(rec["nodeid"] or "<none>").split("::", 1)[0]] += 1
            slot["src_frames"][rec["src_frame"]] += 1
    result = {}
    for port, slot in sorted(by_port.items()):
        result[str(port)] = {
            "connects": slot["connects"],
            "refused": slot["refused"],
            "distinct_tests": len(slot["tests"]),
            "distinct_files": len(slot["files"]),
            "phases": dict(slot["phases"]),
            "threads": dict(slot["threads"]),
            "src_frames": dict(slot["src_frames"].most_common(8)),
            "tests": sorted(t or "<none>" for t in slot["tests"]) if slot["connects"] <= 60 or port in (8050, 8200, 8201, 8202) else f"{len(slot['tests'])} tests (see jsonl)",
            "files_by_count": dict(slot["files"].most_common()),
        }
    return result


def main() -> int:
    worktree = Path(sys.argv[1]).resolve()
    label = sys.argv[2]
    out = SCRATCH / "runs" / label
    out.mkdir(parents=True, exist_ok=True)
    env, dropped = child_env()
    print(f"child env: dropped {dropped} JUNIPER_/CASCOR_/CANOPY_ variables (names not recorded)")
    ids = collect(worktree, env, out)
    if "--collect-only" in sys.argv[3:]:
        return 0
    if not ids:
        print("no node ids collected: refusing to run (an empty group would fall back to testpaths, the whole suite)")
        return 2
    groups = split(ids)
    if not all(groups):
        print("an empty group would fall back to testpaths: refusing to run")
        return 2
    procs = []
    for index, files in enumerate(groups, start=1):
        basetemp = worktree / "tmp" / f"valbt-{label}-g{index}"
        args = [PY, str(RUNNER), str(out / f"census_g{index}.jsonl"), "-m", SELECTOR, *files, "-p", "no:cacheprovider", "--timeout=60", f"--basetemp={basetemp}", f"--junitxml={out / f'junit_g{index}.xml'}", "-q", "-rfE", "--no-header"]
        log = (out / f"pytest_g{index}.log").open("w", encoding="utf-8")
        procs.append((subprocess.Popen(args, cwd=worktree, env=env, stdout=log, stderr=subprocess.STDOUT), log))  # nosec B603
    codes = []
    for proc, log in procs:
        codes.append(proc.wait())
        log.close()
    summary = {
        "worktree": str(worktree),
        "label": label,
        "selected_ids": len(ids),
        "exit_codes": codes,
        "junit": {f"g{i}": junit_summary(out / f"junit_g{i}.xml") for i in range(1, GROUPS + 1)},
        "census": census_summary([out / f"census_g{i}.jsonl" for i in range(1, GROUPS + 1)]),
    }
    totals = Counter()
    for part in summary["junit"].values():
        for key in ("tests", "failures", "errors", "skipped"):
            totals[key] += int(part.get(key) or 0)
    summary["junit_totals"] = dict(totals)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"exit_codes": codes, "junit_totals": summary["junit_totals"], "failed": [f for part in summary["junit"].values() for f in part.get("failed", [])]}, indent=1))
    print(json.dumps({port: {k: v for k, v in data.items() if k in ("connects", "refused", "distinct_tests", "distinct_files", "phases", "threads")} for port, data in summary["census"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
