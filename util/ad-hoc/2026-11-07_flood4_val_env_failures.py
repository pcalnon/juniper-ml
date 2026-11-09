"""
Flood-4 validation: run the builder's 14 reported environmental failures (5 regression suites run alone +
the juniper-ci-tools suite) in TWO trees -- this carrier worktree and a clean origin/main worktree -- with
the SAME interpreter and the SAME environment (TMPDIR = juniper-ml/tmp, inherited GIT_CEILING_DIRECTORIES),
and compare the failing test ids and each failure's last exception line.

Usage: python3 <this> <out.json> <carrier_tree> <clean_main_tree>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens), item 5
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SUITES = ["tests/test_a0_restore_scripts.py", "tests/test_configure_commit_signing.py", "tests/test_e2e_f037_render_census.py", "tests/test_replay_redrive_stack_refusal.py", "tests/test_workflow_script_paths.py"]
PY = sys.executable


def unittest_run(tree: Path, suite: str) -> dict[str, object]:
    r = subprocess.run([PY, "-m", "unittest", "-v", suite], cwd=tree, capture_output=True, text=True, timeout=1200)
    text = r.stdout + r.stderr
    failed = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\S+ \([^)]*\))", text, re.M)))
    blocks = re.split(r"^={50,}$", text, flags=re.M)
    reasons = {}
    for b in blocks:
        m = re.search(r"^(?:FAIL|ERROR): (\S+ \([^)]*\))", b, re.M)
        if m:
            lines = [l for l in b.strip().splitlines() if l.strip() and not l.startswith("-" * 20)]
            exc = [l for l in lines if re.match(r"^\w*(Error|Exception|AssertionError)\b", l)]
            reasons[m.group(1)] = (exc[-1] if exc else lines[-1])[:300]
    ran = re.search(r"^Ran (\d+) tests?", text, re.M)
    return {"rc": r.returncode, "ran": int(ran.group(1)) if ran else None, "failed": failed, "reasons": reasons, "tail": text.strip().splitlines()[-1:]}


def pytest_ci_tools(tree: Path) -> dict[str, object]:
    env = dict(os.environ, PYTHONPATH=str(tree / "juniper-ci-tools"))
    r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE"], cwd=tree / "juniper-ci-tools", capture_output=True, text=True, timeout=1800, env=env)
    text = r.stdout + r.stderr
    failed = sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+)", text, re.M)))
    reasons = {}
    for m in re.finditer(r"^(?:FAILED|ERROR) (\S+)(?: - (.*))?$", text, re.M):
        reasons[m.group(1)] = (m.group(2) or "")[:300]
    summary = [l for l in text.splitlines() if re.search(r"\d+ (passed|failed)", l)]
    return {"rc": r.returncode, "failed": failed, "reasons": reasons, "summary": summary[-1:] if summary else []}


def main() -> int:
    out = Path(sys.argv[1])
    trees = {"carrier": Path(sys.argv[2]), "clean_main": Path(sys.argv[3])}
    res: dict[str, dict[str, object]] = {"env": {"python": PY, "TMPDIR": os.environ.get("TMPDIR"), "GIT_CEILING_DIRECTORIES": os.environ.get("GIT_CEILING_DIRECTORIES")}}
    for name, tree in trees.items():
        res[name] = {s: unittest_run(tree, s) for s in SUITES}
        res[name]["juniper-ci-tools"] = pytest_ci_tools(tree)
    cmp = {}
    for key in SUITES + ["juniper-ci-tools"]:
        a, b = res["carrier"][key], res["clean_main"][key]
        cmp[key] = {"same_failed_ids": a["failed"] == b["failed"], "carrier_failed": len(a["failed"]), "main_failed": len(b["failed"]), "same_reasons": a["reasons"] == b["reasons"], "only_in_carrier": sorted(set(a["failed"]) - set(b["failed"])), "only_in_main": sorted(set(b["failed"]) - set(a["failed"]))}
    res["comparison"] = cmp
    out.write_text(json.dumps(res, indent=2) + "\n")
    for k, v in cmp.items():
        print(k, v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
