#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 round-2 validation (ad hoc)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""T-F1 round 2: with the empty-payload guard disabled, do the poisoned-jq cases write under
tmp_path (and fail on `not result.body.exists()`) rather than under the system temp dir?

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-canopy#797 tests carrier, validation round 2, correction T-F1 (findings: tmp/flood4/canopy/val-round2/)

Builds a minimal tree in the scratch dir (never in the carrier): the carrier's
lockfile-update.yml with `if [ -z "${LOCK_B64}" ]; then` -> `if false; then`, and the carrier's
test file, at the same relative paths (the test finds the workflow via parents[3]). Runs it
under strace (file syscalls) with --noconftest, then reports per-test outcomes, every
lockfile-commit*.json open, and any write under the system temp dirs.

Usage: python3 <this> <carrier> <scratch dir>
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

GUARD = 'if [ -z "${LOCK_B64}" ]; then'


def main() -> int:
    carrier, scratch = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    tree = scratch / "tf1_mut_tree"
    if tree.exists():
        shutil.rmtree(tree)
    (tree / ".github" / "workflows").mkdir(parents=True)
    (tree / "src" / "tests" / "regression").mkdir(parents=True)
    wf = (carrier / ".github" / "workflows" / "lockfile-update.yml").read_text()
    assert wf.count(GUARD) == 1, wf.count(GUARD)
    (tree / ".github" / "workflows" / "lockfile-update.yml").write_text(wf.replace(GUARD, "if false; then"))
    shutil.copy2(carrier / "src" / "tests" / "regression" / "test_lockfile_regen_empty_payload.py", tree / "src" / "tests" / "regression" / "test_lockfile_regen_empty_payload.py")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(scratch), GIT_CONFIG_GLOBAL=os.devnull)
    trace = scratch / "tf1_mut_strace.log"
    cmd = ["timeout", "600", "strace", "-f", "-qq", "-e", "signal=none", "-e", "trace=open,openat,creat,rename,renameat,renameat2,unlink,unlinkat", "-o", str(trace),
           "/opt/miniforge3/bin/conda", "run", "--no-capture-output", "-n", "JuniperCanopy1", "python", "-m", "pytest", "--noconftest", "-p", "no:cacheprovider", "-o", "addopts=",
           f"--basetemp={scratch / 'bt_tf1_mut'}", "-q", "-rA", "src/tests/regression/test_lockfile_regen_empty_payload.py"]
    p = subprocess.run(cmd, cwd=tree, env=env, capture_output=True, text=True)
    (scratch / "tf1_mut_pytest.log").write_text(p.stdout + "\n--- stderr ---\n" + p.stderr)
    outcomes = re.findall(r"^(PASSED|FAILED|ERROR) (\S+)", p.stdout, flags=re.M)
    tmp_writes, opens = [], []
    for line in trace.read_text(errors="replace").splitlines():
        m = re.search(r'\((?:[^,]*, )?"([^"]+)"', line)
        if not m:
            continue
        path = m.group(1)
        if "lockfile-commit" in path:
            opens.append(line.strip()[:260])
        if path.startswith(("/tmp/", "/var/tmp/")) and re.search(r"O_WRONLY|O_RDWR|O_CREAT|O_TRUNC|creat\(|rename|unlink", line) and "= -1" not in line:  # tmp-path-literal: allow (detector: reads the system temp dir, never writes it)
            tmp_writes.append(line.strip()[:260])
    summary = {"exit": p.returncode, "outcomes": outcomes, "lockfile_commit_opens": opens, "tmp_writes": tmp_writes,
               "tmp_lockfile_entries_after": sorted(n for n in os.listdir("/tmp") if "lockfile" in n.lower())}  # tmp-path-literal: allow (detector: reads the system temp dir, never writes it)
    (scratch / "tf1_mut_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
