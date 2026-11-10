#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 round-2 validation (ad hoc)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""Round-2 interdiff: what the correction pass changed in a carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-canopy#802 docs carrier, validation round 2, the exact correction set (findings: tmp/flood4/canopy/val-round2/)

Reconstructs the round-1 state of every file a carrier touches (main's blob
+ the round-1 validator's saved diff, applied with the `patch` program in a
scratch directory), then diffs that state against the carrier worktree's
current file. Read-only on the carrier and on the canopy primary.

Usage:
  python3 <this> <canopy primary> <base sha> <round-1 diff> <carrier worktree> <out dir>
"""
import difflib
import pathlib
import re
import shutil
import subprocess
import sys


def main() -> int:
    primary, base, r1_diff, carrier, out = sys.argv[1:6]
    out_dir = pathlib.Path(out)
    stage = out_dir / "interdiff_r1_state"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    diff_text = pathlib.Path(r1_diff).read_text()
    r1_paths = re.findall(r"^diff --git a/(\S+) b/\S+$", diff_text, flags=re.M)
    cur = subprocess.run(["git", "-C", carrier, "diff", "--name-only"], capture_output=True, text=True, check=True).stdout.split()
    paths = sorted(set(r1_paths) | set(cur))
    for p in paths:
        dst = stage / p
        dst.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.run(["git", "-C", primary, "show", f"{base}:{p}"], capture_output=True, check=True).stdout
        dst.write_bytes(blob)
    res = subprocess.run(["patch", "-p1", "-d", str(stage), "--no-backup-if-mismatch", "-i", str(pathlib.Path(r1_diff).resolve())], capture_output=True, text=True)
    report = [f"patch exit={res.returncode}", res.stdout.strip(), res.stderr.strip(), f"r1 files: {len(r1_paths)}; current files: {len(cur)}", ""]
    for p in paths:
        r1 = (stage / p).read_text().splitlines(keepends=True)
        now = (pathlib.Path(carrier) / p).read_text().splitlines(keepends=True)
        d = list(difflib.unified_diff(r1, now, fromfile=f"r1/{p}", tofile=f"now/{p}", n=2))
        if d:
            report.append("".join(d))
        else:
            report.append(f"== {p}: unchanged since round 1\n")
    (out_dir / "interdiff_r1_to_now.patch").write_text("\n".join(report))
    print(f"wrote {out_dir / 'interdiff_r1_to_now.patch'}; patch exit={res.returncode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
