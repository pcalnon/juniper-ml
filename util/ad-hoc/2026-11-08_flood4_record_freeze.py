#!/usr/bin/env python3
"""
Freeze the flood-4 record PR's validated files into a snapshot for the signed batch push.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 disposition record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (sec 9);
         util/ad-hoc/2026-11-07_flood4_signed_push_batches.py (consumes the snapshot and the path list);
         util/ad-hoc/2026-11-07_flood4_prep_pr_texts.py (the carriers' equivalent, which refuses util/ad-hoc/)

WHY THIS EXISTS
The signed upload sends whole files, so what goes up must be exactly what was validated, not whatever the
worktree holds when the push runs. The carriers' prep script refuses util/ad-hoc/ paths by design, because
the provenance scripts were always meant for this record's PR, so the record needs its own freeze. It copies
the record's path set into <out>/snapshot/ at repo-relative paths, writes <out>/paths.txt and
<out>/snapshot.sha256, and refuses if the snapshot already exists (a snapshot is frozen once), if a path is
missing, or if any path other than CHANGELOG.md already exists at --base-sha (every other file is new).

Usage (from the repository root):
  2026-11-08_flood4_record_freeze.py --base-sha <sha> --out tmp/flood4/push/ml-record
"""

import argparse
import glob
import hashlib
import os
import shutil
import subprocess
import sys

FIXED = [
    "notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md",
    "CHANGELOG.md",
    "prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md",
    "prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-record-validated-fixes-built-round2-triaged.md",
]
GLOBS = [
    "reports/2026-11-08_flood4-disposition/*",
    "util/ad-hoc/2026-11-07_flood4_*.py",
    "util/ad-hoc/2026-11-08_flood4_*.py",
]
MODIFIED_OK = {"CHANGELOG.md"}


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def exists_at(sha, path):
    p = subprocess.run(["git", "cat-file", "-e", "%s:%s" % (sha, path)], capture_output=True)
    return p.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-sha", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    snap = os.path.join(a.out, "snapshot")
    if os.path.exists(snap):
        raise SystemExit("REFUSED: %s exists; a snapshot is frozen once taken" % snap)
    paths = list(FIXED)
    for g in GLOBS:
        paths += sorted(p for p in glob.glob(g) if os.path.isfile(p))
    missing = [p for p in paths if not os.path.isfile(p)]
    if missing:
        raise SystemExit("REFUSED: missing %s" % missing)
    clobber = [p for p in paths if p not in MODIFIED_OK and exists_at(a.base_sha, p)]
    if clobber:
        raise SystemExit("REFUSED: these exist at %s and would be overwritten: %s" % (a.base_sha, clobber))
    if not all(exists_at(a.base_sha, p) for p in MODIFIED_OK):
        raise SystemExit("REFUSED: CHANGELOG.md is absent at the base")
    os.makedirs(snap)
    lines = []
    for p in paths:
        dst = os.path.join(snap, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(p, dst)
        lines.append("%s  %s" % (sha256(dst), p))
    with open(os.path.join(a.out, "paths.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(paths) + "\n")
    with open(os.path.join(a.out, "snapshot.sha256"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    total = sum(os.path.getsize(os.path.join(snap, p)) for p in paths)
    print("froze %d paths (%d bytes) into %s" % (len(paths), total, snap))
    return 0


if __name__ == "__main__":
    sys.exit(main())
