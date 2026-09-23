#!/usr/bin/env python3
"""Say WHERE section 10.2 step 1's restore drill is discharged, and why it cannot precede P0.

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-09-23
Status:      ad-hoc -- document-of-record edit
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-09-23_record_smart_result.py (wrote the row this corrects)

THE AMBIGUITY THIS CLOSES. Section 10.2 opens "it runs *after* the recovery, not during it", and its
step 1 reads "SMART test sda; restore-drill the CURRENT set". Those two together invite the reading
that a drill should be run NOW, before P0 -- and an operator who tries discovers there is nothing to
drill against, because the drill needs the job index that P0 step 1's freeze copies aside. The SMART
half genuinely did run early and correctly, which makes the drill half look equally ready. It is not.

Carries both guards from the 2026-09-22 run: `edit()` refuses an edit whose `old` is a substring of
its `new`, and the over-width scan runs BEFORE the write.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DESIGN = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")

EDITS: list[tuple[str, str, str, int]] = []


def edit(tag: str, old: str, new: str, count: int = 1) -> None:
    if old in new:
        raise SystemExit(f"NON-IDEMPOTENT edit {tag!r}: `old` is a substring of `new`")
    EDITS.append((tag, old, new, count))


edit(
    "step 1 row names where the drill is discharged",
    "| 1 | SMART test `sda` — **DONE 2026-09-23, PASSED** (note 10.2a). Restore-drill the CURRENT set — **still outstanding** | the drill passes on the current passphrase |",
    "| 1 | SMART test `sda` — **DONE 2026-09-23, PASSED** (note 10.2a). Restore-drill the CURRENT set — outstanding, and **discharged by AC-4's pre-recovery drill inside §8 P0 step 11**, not before P0 (note 10.2c) | AC-4's first drill passes on the current passphrase |",
)

edit(
    "note 10.2c",
    """  This **closes** the \u00a712 / D-12a carried item "sda SMART never read".
- **(10.2b)** **Staging goes on `nvme0n1p5` (`/`), not on `sda`.**""",
    """  This **closes** the \u00a712 / D-12a carried item "sda SMART never read".
- **(10.2c)** **Step 1's drill cannot precede P0, and does not add a second drill.** The SMART half ran
  early and correctly; the drill half cannot, for a reason that is easy to miss because the two halves sit
  in one row. A drill needs a **job index**, and P0 step 0(c) already records that the index must come from
  **P0 step 1's freeze** — `--no-local-db` rebuilds it from all 877 dindex volumes and was measured at
  ">30 minutes for a single small file here, without completing"
  (`util/ad-hoc/duplicati_drill_run.py`). The distinction that makes a drill possible at all is that the
  **server** database is the file locked under an unmatched key (§5.4), while the **job** index —
  `BMXWPAOGLP.sqlite`, last written 09-18 — is a separate file and is what a drill reads. So the drill is
  **AC-4's first one** — from `duplicati-20260918T140000Z`, the pre-recovery fileset — run at §8 P0 step 11
  alongside the post-recovery drill. §10.2 step 1 names that drill as its gate; it does not ask for another.
  Its terms are §3.3 item 6's and are not negotiable by whoever runs it: never pass
  `--restore-with-local-blocks` (`--no-local-blocks` is **deprecated** in 2.4.0.0 because not using local
  blocks is now the default), select by `--time=`, compare **SHA-256 and length** on ≥ 15 files, include a
  negative control that must fail, and treat the **exit code as not evidence**.
- **(10.2b)** **Staging goes on `nvme0n1p5` (`/`), not on `sda`.**""",
)

edit(
    "closing paragraph states the real next action",
    """**Step 1 is first, is not optional, and is currently HALF DONE**: the SMART half passed on
2026-09-23, the restore drill has not run, so step 2 is not yet unblocked.""",
    """**Step 1 is first, is not optional, and is currently HALF DONE**: the SMART half passed on
2026-09-23; the drill half is AC-4's and runs inside P0 (note 10.2c), so step 2 is not unblocked and
**the next action in this arc is §8's P0 recovery, not anything in §10.2**.""",
)


def main() -> int:
    if not DESIGN.is_file():
        print(f"FATAL: {DESIGN} not found", file=sys.stderr)
        return 2

    text = DESIGN.read_text(encoding="utf-8")
    original = text
    failures: list[str] = []
    applied = skipped = 0

    for tag, old, new, count in EDITS:
        have = text.count(old)
        if have == count:
            text = text.replace(old, new, count)
            applied += 1
            print(f"  OK       {tag}")
        elif text.count(new) >= 1 and have == 0:
            skipped += 1
            print(f"  ALREADY  {tag}")
        else:
            failures.append(tag)
            print(f"  FAIL     {tag}: anchor found {have}x, expected {count}x", file=sys.stderr)

    if failures:
        print(f"\n{len(failures)} anchor(s) failed; NOTHING written.", file=sys.stderr)
        return 1
    if text == original:
        print(f"\nno change ({skipped} already applied) -- idempotent")
        return 0

    over = [(n, len(line)) for n, line in enumerate(text.split("\n"), 1) if len(line) > 512]
    for n, width in over:
        print(f"  OVER-WIDTH line {n}: {width} chars", file=sys.stderr)
    if over:
        print(f"  {len(over)} line(s) exceed 512 -- NOTHING written", file=sys.stderr)
        return 3

    DESIGN.write_text(text, encoding="utf-8")
    print(f"\napplied {applied}, already {skipped}; {DESIGN} now {len(text.splitlines())} lines")
    subprocess.run(["git", "diff", "--stat", "--", str(DESIGN)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
