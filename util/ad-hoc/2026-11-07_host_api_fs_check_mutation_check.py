#!/usr/bin/env python3
"""
Mutation check: tests/test_host_api_filesystems_check.py must FAIL on every seeded defect.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (test-efficacy evidence)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/host_api_filesystems_check.py, tests/test_host_api_filesystems_check.py,
         notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md

A green suite proves nothing if it would also pass a broken checker. Each mutant below re-creates
a plausible defect -- several are the exact failure of the 2026-10-27 repair (judging by unit
files, not by the mount table) -- and the suite is run against the mutant through
HOST_API_FS_CHECK_SCRIPT. A mutant the suite does not kill is reported as SURVIVED and the script
exits 1.

Each mutant is written to a fresh file under the repo's tmp/ (never /tmp), run with
PYTHONDONTWRITEBYTECODE=1 so no stale .pyc can stand in for it, and the suite's exit status is
read directly (no pipe).

Usage: python3 util/ad-hoc/2026-11-07_host_api_fs_check_mutation_check.py
Exit: 0 every mutant killed; 1 a mutant survived or an edit did not apply.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "util" / "host_api_filesystems_check.py"
SUITE = "tests/test_host_api_filesystems_check.py"

# (name, old, new): `old` must occur exactly once in the checker.
MUTANTS = [
    ("bpf loses mode=0700", '"options": "nosuid,nodev,noexec,mode=0700"', '"options": "nosuid,nodev,noexec"'),
    ("securityfs treated as a unit-file mount", '"fstype": "securityfs", "origin": "pid1"', '"fstype": "securityfs", "origin": "unit"'),
    ("repair-scoped: only unit-file mounts are judged", "    for spec in API_MOUNTS:\n", "    for spec in [s for s in API_MOUNTS if s[\"origin\"] == \"unit\"]:\n"),
    ("AppArmor consistency never fails", "    consistent = interface or not enabled\n", "    consistent = True\n"),
    ("first mount at a point wins", "        top[mount.where] = mount\n", "        top.setdefault(mount.where, mount)\n"),
    ("applicability ignored", '        if spec["applies_if"] and not exists(spec["applies_if"]) and mount is None:\n', "        if False:\n"),
    ("CLI always exits 0", "    return 0 if report.host_ok else 1\n", "    return 0\n"),
    ("octal escapes not decoded", "    return _OCTAL.sub(lambda m: chr(int(m.group(1), 8)), path)\n", "    return path\n"),
    ("fstype not compared", '        elif mount.fstype != spec["fstype"]:\n', "        elif False:\n"),
    ("module parameter Y not recognised", '    enabled = enabled_raw.startswith("Y")\n', '    enabled = enabled_raw == "Yes"\n'),
    ("fstype read from the source field", "fstype=rest[0]", "fstype=rest[1] if len(rest) > 1 else rest[0]"),
]


def main() -> int:
    source = SCRIPT.read_text(encoding="utf-8")
    tmp_root = Path(os.environ.get("TMPDIR") or (REPO / "tmp"))
    tmp_root.mkdir(parents=True, exist_ok=True)
    failures = 0
    with tempfile.TemporaryDirectory(dir=tmp_root, prefix="host_api_fs_mutants_") as work:
        baseline = subprocess.run([sys.executable, "-m", "unittest", SUITE], cwd=REPO, capture_output=True, text=True, check=False)
        print(f"baseline (unmutated): exit={baseline.returncode}")
        if baseline.returncode != 0:
            print(baseline.stdout[-2000:] + baseline.stderr[-2000:])
            return 1
        for index, (name, old, new) in enumerate(MUTANTS, 1):
            if source.count(old) != 1:
                print(f"[EDIT-FAILED] {name}: anchor occurs {source.count(old)} times")
                failures += 1
                continue
            mutant = Path(work) / f"mutant_{index:02d}.py"
            mutant.write_text(source.replace(old, new), encoding="utf-8")
            env = dict(os.environ, HOST_API_FS_CHECK_SCRIPT=str(mutant), PYTHONDONTWRITEBYTECODE="1")
            result = subprocess.run([sys.executable, "-m", "unittest", SUITE], cwd=REPO, env=env, capture_output=True, text=True, check=False)
            verdict = "KILLED" if result.returncode != 0 else "SURVIVED"
            if verdict == "SURVIVED":
                failures += 1
            tail = [line for line in result.stderr.splitlines() if line.startswith(("FAILED", "OK"))]
            print(f"[{verdict}] {name}  ({tail[-1] if tail else 'no summary'})")
    print(f"{len(MUTANTS) - failures} of {len(MUTANTS)} mutants killed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
