"""
Re-run, under the census runner, every canopy test FILE whose tests errored in setup on a vanished --basetemp.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 round-2 validation of the owner's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/BRIEF_VALIDATE_R2.txt)

Usage:
    python3 util/ad-hoc/2026-11-09_flood4r2_val_r17-canopy-guard_rerun_errored.py <worktree> <label>

During the lane runs of runs/<label>/ the worktree's tmp/ directory (holding each group's --basetemp) was deleted by
something outside this validator's scripts, so every test that needed tmp_path afterwards errored in setup with
FileNotFoundError and never ran. This maps those junit test cases to their files, re-runs the whole files in one
process with a fresh basetemp (CI's selector and step env), and writes junit + census JSONL to runs/<label>-rerun/.
The merged view takes the first run for every other file and the rerun for these files (a file-level partition).
"""

from __future__ import annotations

import json
import os
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


def errored_files(worktree: Path, label: str) -> list[str]:
    files = set()
    for junit in sorted((SCRATCH / "runs" / label).glob("junit_g*.xml")):
        root = ET.parse(junit).getroot()  # nosec B314
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        for case in suite.iter("testcase"):
            node = case.find("error")
            if node is None or "valbt-" not in (node.get("message") or ""):
                continue
            parts = case.get("classname").split(".")
            for cut in range(len(parts), 0, -1):
                candidate = "/".join(parts[:cut]) + ".py"
                if (worktree / candidate).is_file():
                    files.add(candidate)
                    break
    return sorted(files)


def main() -> int:
    worktree = Path(sys.argv[1]).resolve()
    label = sys.argv[2]
    files = errored_files(worktree, label)
    out = SCRATCH / "runs" / f"{label}-rerun"
    out.mkdir(parents=True, exist_ok=True)
    (out / "files.txt").write_text("\n".join(files) + "\n", encoding="utf-8")
    print(f"{label}: {len(files)} files to re-run")
    if not files:
        return 0
    (worktree / "tmp").mkdir(exist_ok=True)
    env = dict(os.environ)
    for name in [name for name in env if name.startswith(("JUNIPER_", "CASCOR_", "CANOPY_"))]:
        env.pop(name)
    env.pop("LD_LIBRARY_PATH", None)
    env.update(LIBTORCH="", CASCOR_BACKEND_AVAILABLE="0", RUN_SERVER_TESTS="0", ENABLE_SLOW_TESTS="0", PYTHONDONTWRITEBYTECODE="1")
    argv = [PY, str(RUNNER), str(out / "census.jsonl"), "-m", SELECTOR, *files, "-p", "no:cacheprovider", "--timeout=60", f"--basetemp={worktree / 'tmp' / ('valbt-' + label + '-rerun')}", f"--junitxml={out / 'junit.xml'}", "-q", "-rfE", "--no-header"]
    with (out / "pytest.log").open("w", encoding="utf-8") as log:
        code = subprocess.run(argv, cwd=worktree, env=env, stdout=log, stderr=subprocess.STDOUT).returncode  # nosec B603
    root = ET.parse(out / "junit.xml").getroot()  # nosec B314
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    failed = []
    for case in suite.iter("testcase"):
        node = case.find("failure") if case.find("failure") is not None else case.find("error")
        if node is not None:
            failed.append(f"{case.get('classname')}::{case.get('name')} | {(node.get('message') or '')[:200]}")
    rerun_files = set(files)
    merged: dict[int, dict] = defaultdict(lambda: {"connects": 0, "tests": set(), "files": set(), "phases": Counter()})
    sources = [(p, False) for p in sorted((SCRATCH / "runs" / label).glob("census_g*.jsonl"))] + [(out / "census.jsonl", True)]
    for path, is_rerun in sources:
        for line in path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            test_file = (rec["nodeid"] or "<none>").split("::", 1)[0]
            if (test_file in rerun_files) != is_rerun:
                continue
            slot = merged[rec["port"]]
            slot["connects"] += 1
            slot["tests"].add(rec["nodeid"])
            slot["files"].add(test_file)
            slot["phases"][rec["phase"]] += 1
    merged_view = {str(port): {"connects": s["connects"], "distinct_tests": len(s["tests"]), "distinct_files": len(s["files"]), "phases": dict(s["phases"]), "tests": sorted(t for t in s["tests"] if t) if port in (8050, 8200, 8201, 8202) else None} for port, s in sorted(merged.items())}
    summary = {"exit": code, "junit": {k: suite.get(k) for k in ("tests", "failures", "errors", "skipped")}, "failed": failed, "merged_census": merged_view}
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "merged_census"}, indent=1))
    print(json.dumps({port: {k: v for k, v in data.items() if k != "tests"} for port, data in merged_view.items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
