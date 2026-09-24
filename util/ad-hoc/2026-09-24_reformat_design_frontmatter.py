#!/usr/bin/env python3
"""Re-land #2045's front-matter reformat of the backup design, with its continuation fixed.

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-09-24
Status:      ad-hoc -- document-of-record edit
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-09-23_pr2045_net_effect.py (proved this was #2045's ONLY net change)

#2045 carried 669 files and, measured against main rather than against its stale merge-base, changed
exactly one: this document's front matter, from flowing lines into a bulleted block. That is a real
readability gain -- the Companions list in particular is five links run together as bare lines -- so
it is re-landed here on its own, where it can be reviewed as what it is.

ONE CORRECTION TO THE ORIGINAL. #2045 put `Verbatim reports:` at column 0 directly beneath a list
item. Markdown treats that as a LAZY CONTINUATION: it renders as part of the bullet, so the output
looks right while the source says something else, and the next editor who inserts a blank line above
it silently breaks the list. Indented to two spaces here, which is what the renderer was inferring.

Carries the guards from the 2026-09-22 run: `edit()` refuses an edit whose `old` is a substring of
its `new`, and the over-width scan runs BEFORE the write.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DESIGN = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")

OLD = """**Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
**Author**: Paul Calnon
**Date**: 2026-09-21
**Status**: VALIDATED (round 2) — consensus round 1 (six validators) and round 2 (four lanes) have
both reported, and every finding is applied or recorded as dissent in §11. Verbatim reports:
`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` and
`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`.
**§8 is executable in this order and no other**: **P0.5a** items 1–2, then **P0 step −1** (review and
merge the nine scripts §8 invokes that are now staged; the tenth is a P3 deliverable), then **P0 step 0**'s
owner gates, then **P0**, then **P0.5b** (the re-key, which needs the recovered data folder). Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved except the one escrow copy named
in P1 step 4.
**Supersedes in part**: the *Dropbox-era* operating state; does **not** supersede the certification record
**Companions**:
[`JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md`](JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md) (the design of record, "PLAN"),
[`JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`](JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md) (the certification record, "YAM"),
[`JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`](JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md) ("DMG"),
[`JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md`](JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md) ("GPG"),
[`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) ("CON", the validation procedure this document is held to)."""

NEW = """- **Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
- **Author**: Paul Calnon
- **Date**: 2026-09-21
- **Status**: VALIDATED (round 2) — consensus round 1 (six validators) and round 2 (four lanes) have both reported, and every finding is applied or recorded as dissent in §11.
  Verbatim reports:
  - `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`
  - `JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`
- **§8 is executable in this order and no other**: **P0.5a** items 1–2, then **P0 step −1** (review and merge the nine scripts §8 invokes that are now staged; the tenth is a P3 deliverable), then **P0 step 0**'s owner gates, then **P0**, then **P0.5b** (the re-key, which needs the recovered data folder).
  - Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved except the one escrow copy named in P1 step 4.
- **Supersedes in part**: the *Dropbox-era* operating state; does **not** supersede the certification record
- **Companions**:
  - [`JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md`](JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md) (the design of record, "PLAN"),
  - [`JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`](JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md) (the certification record, "YAM"),
  - [`JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`](JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md) ("DMG"),
  - [`JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md`](JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md) ("GPG"),
  - [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) ("CON", the validation procedure this document is held to)."""


def main() -> int:
    if not DESIGN.is_file():
        print(f"FATAL: {DESIGN} not found", file=sys.stderr)
        return 2
    if OLD in NEW:
        raise SystemExit("NON-IDEMPOTENT: `old` is a substring of `new`")

    text = DESIGN.read_text(encoding="utf-8")
    have = text.count(OLD)
    if have == 0 and text.count(NEW) == 1:
        print("ALREADY applied -- idempotent")
        return 0
    if have != 1:
        print(f"FAIL: front-matter anchor found {have}x, expected 1x; NOTHING written", file=sys.stderr)
        return 1

    text = text.replace(OLD, NEW, 1)

    over = [(n, len(line)) for n, line in enumerate(text.split("\n"), 1) if len(line) > 512]
    for n, width in over:
        print(f"  OVER-WIDTH line {n}: {width} chars", file=sys.stderr)
    if over:
        print(f"  {len(over)} line(s) exceed 512 -- NOTHING written", file=sys.stderr)
        return 3

    DESIGN.write_text(text, encoding="utf-8")
    print(f"front matter reformatted; {DESIGN} now {len(text.splitlines())} lines")
    subprocess.run(["git", "diff", "--stat", "--", str(DESIGN)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
