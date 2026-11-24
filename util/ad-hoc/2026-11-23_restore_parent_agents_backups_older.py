#!/usr/bin/env python3
"""Restore the six OLDER parent AGENTS.md backups that the blind "owner -> Overtoad" pass rewrote, hash-verified.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups: remaining-task inventory item R56)
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- one-off (restores six backup files in juniper-ml's primary tmp/)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-23_restore_parent_agents_backups.py (the same restore for the 2026-11-14/15 backups);
         notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md (item R56)

Why
---
The parent ``Juniper/AGENTS.md`` is unversioned, so its backups in juniper-ml's primary ``tmp/`` are its only history.
The blind pass of 2026-11-20 rewrote all six of the older ones as well, so none matched its record. Each recorded sha256
comes from a source written before the pass:

- ``2026-10-29-parent-agents-md-backups/``: ``6ffd7604`` (pre-edit) and ``79b17d5e`` (after the first edit), from
  ``prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_recurrence-equities-mnist-schema-probe-canopy-778-parent-agents-cascor-0-13-0.md`` line 92;
- ``2026-11-01-parent-agents-md-backup/``: ``5082c9c8`` -> ``29e375ff``, from
  ``prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-01_recurrence-equities-apd-ml-002-closed-parent-agents-edited-owner-items-next.md`` line 23;
- ``2026-11-07-parent-agents-md-backup/``: ``29e375ff`` -> ``48e2568a``, from
  ``notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`` line 677 (v1.15.17).

The inverse ("The Overtoad" -> "Owner", then "Overtoad" -> "owner") reproduces every one of them. Per file: refuse
unless it does; keep the rewritten bytes as ``<name>.substituted-2026-11-20`` (never overwritten); write the restored
bytes; re-read and re-verify.

Usage
-----
    python3 util/ad-hoc/2026-11-23_restore_parent_agents_backups_older.py            # dry run
    python3 util/ad-hoc/2026-11-23_restore_parent_agents_backups_older.py --execute
Exit 0 when every file is restored (or already original); 2 when any refuses.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

BASE = Path.home() / "Development/python/Juniper/juniper-ml/tmp"
CASES = (
    ("2026-10-29-parent-agents-md-backups/AGENTS.md.pre-edit-2026-10-27T22-35Z", "6ffd7604"),
    ("2026-10-29-parent-agents-md-backups/AGENTS.md.after-first-edit-2026-10-29T20-30Z", "79b17d5e"),
    ("2026-11-01-parent-agents-md-backup/AGENTS.md.before-deploy-pin-edit", "5082c9c8"),
    ("2026-11-01-parent-agents-md-backup/AGENTS.md.after-deploy-pin-edit", "29e375ff"),
    ("2026-11-07-parent-agents-md-backup/AGENTS.md.before-juniper-ml-0-11-4-edit", "29e375ff"),
    ("2026-11-07-parent-agents-md-backup/AGENTS.md.after-juniper-ml-0-11-4-edit", "48e2568a"),
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
