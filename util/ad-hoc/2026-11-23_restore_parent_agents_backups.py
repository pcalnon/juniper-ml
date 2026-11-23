#!/usr/bin/env python3
"""Restore the parent AGENTS.md backups that the blind "owner -> Overtoad" pass rewrote, hash-verified.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups: worktree housekeeping)
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- one-off (restores three backup files in juniper-ml's primary tmp/)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-23_r_obs_sc_2_housekeeping.bash (the cleanup whose precondition this repairs);
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md ("The parent's prior copy is
         safe in juniper-ml/tmp/2026-11-14-parent-agents-md-backup/... before buzzing-growing-whale goes")

Why
---
The R-OBS-SC-2 sessions backed up the parent ``Juniper/AGENTS.md`` (unversioned: no git history) before each edit,
and recorded its sha256 around the edits: ``90df2783`` before the 2026-11-14 edit, ``f3f69b34`` after it, ``3009c3f4``
after the 2026-11-15 edit (the handoffs of 2026-11-13 and 2026-11-15). On 2026-11-20 the blind "owner -> Overtoad"
pass rewrote all three backup files (mapping "Owner" to "The Overtoad" and "owner" to "Overtoad"), so none of them
matched its record any more. The inverse ("The Overtoad" -> "Owner", then "Overtoad" -> "owner") reproduces each
recorded prefix exactly, so the originals are restored with proof, not reconstructed.

For each file: refuse unless the inverse reproduces the recorded prefix; keep the rewritten bytes beside it as
``<name>.substituted-2026-11-20`` (never overwritten if present); write the restored bytes; re-read and re-verify.

Usage
-----
    python3 util/ad-hoc/2026-11-23_restore_parent_agents_backups.py            # dry run
    python3 util/ad-hoc/2026-11-23_restore_parent_agents_backups.py --execute
Exit 0 when every file is restored (or already original); 2 when any refuses.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

BASE = Path.home() / "Development/python/Juniper/juniper-ml/tmp"
CASES = (
    ("2026-11-14-parent-agents-md-backup/AGENTS.md.before-2026-11-14-edit", "90df2783"),
    ("2026-11-15-parent-agents-md-backup/AGENTS.md.before-cascor-0-14-0-canopy-0-10-0-edit", "f3f69b34"),
    ("2026-11-15-parent-agents-md-backup/AGENTS.md.after-cascor-0-14-0-canopy-0-10-0-edit", "3009c3f4"),
)
SUFFIX = ".substituted-2026-11-20"


def prefix(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:8]


def inverse(data: bytes) -> bytes:
    return data.replace(b"The Overtoad", b"Owner").replace(b"Overtoad", b"owner")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    bad = 0
    for rel, want in CASES:
        path = BASE / rel
        raw = path.read_bytes()
        if prefix(raw) == want:
            print(f"ORIGINAL  {rel} ({want})")
            continue
        restored = inverse(raw)
        if prefix(restored) != want:
            print(f"REFUSE    {rel}: as-is {prefix(raw)}, inverse {prefix(restored)}, want {want}")
            bad += 1
            continue
        keep = path.with_name(path.name + SUFFIX)
        print(f"{'RESTORE' if args.execute else 'WOULD'}   {rel}: {prefix(raw)} -> {want}; rewritten kept as {keep.name}")
        if args.execute:
            if not keep.exists():
                keep.write_bytes(raw)
            path.write_bytes(restored)
            if prefix(path.read_bytes()) != want:
                print(f"FAILED    {rel}: re-read does not match {want}")
                bad += 1
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
