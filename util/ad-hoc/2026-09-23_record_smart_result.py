#!/usr/bin/env python3
"""Record the 2026-09-23 sda SMART result and fix the staging target in the design's section 10.2.

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-09-23
Status:      ad-hoc -- document-of-record edit
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-09-22_apply_owner_rulings.py (same contract; this reuses its guards)
             util/ad-hoc/smart_checks_backup-sda.bash (produced the evidence recorded here)

Carries forward both guards that 2026-09-22_apply_owner_rulings.py needed on the day:

  * `edit()` REFUSES an edit whose `old` is a substring of its `new`. Such an edit still matches
    after it lands, so a re-run applies it twice, and the anchor-count check cannot see it.
  * the over-width (MD013) scan runs BEFORE the write, because a check after the write is a report
    and not a gate.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DESIGN = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")

EDITS: list[tuple[str, str, str, int]] = []


def edit(tag: str, old: str, new: str, count: int = 1) -> None:
    if old in new:
        raise SystemExit(
            f"NON-IDEMPOTENT edit {tag!r}: `old` is a substring of `new`, so re-running would "
            f"apply it twice. Widen the anchor to SPAN the insertion point."
        )
    EDITS.append((tag, old, new, count))


# --- section 12 / D-12 carried items: the sda SMART item is now CLOSED ----------------------

edit(
    "carried items (exec summary)",
    "`sda` SMART never read (it now guards the only local copy), the read-only loop probe of the destroyed `sdc4`,",
    "`sda` SMART **read 2026-09-23 and PASSED** (note 10.2a) — closed, the read-only loop probe of the destroyed `sdc4`,",
)

edit(
    "carried items (D-12a)",
    "Carried today: `sda` SMART never read (it guards the only local copy); the `sdc4` read-only loop probe;",
    "Closed 2026-09-23: `sda` SMART — run and PASSED (note 10.2a). Carried today: the `sdc4` read-only loop probe;",
)

# --- section 10.2 hazard 1: a healthy disk does not make an in-place SMR rewrite safe -------

edit(
    "hazard 1 -- SMART result and SMR",
    """1. **`--reupload` deletes the originals at the destination.** The sole local copy sits on `sda`, a disk
   that has never had a SMART test (§12, carried). This is why the ruling is **stage → verify → swap**
   and not in-place, and why nothing here contradicts §8's rule that nothing under
   `/mnt/Backups/Ubuntu/` is deleted or moved.""",
    """1. **`--reupload` deletes the originals at the destination.** The sole local copy sits on `sda`, whose
   SMART state was unknown when this was written and is now **read and PASSED** (2026-09-23, note 10.2a).
   A healthy disk does **not** make an in-place rewrite safe, for a second reason the health report
   itself supplies: `sda` is a **drive-managed SMR** drive (`WDC WD40EZAZ-00SF3B0`, "Western Digital
   Blue (SMR)"), so `--reupload` against the live destination is a full band-rewrite of the only copy —
   slow enough that it must not be mistaken for a hung operation. This is why the ruling is
   **stage → verify → swap** and not in-place, and why nothing here contradicts §8's rule that nothing
   under `/mnt/Backups/Ubuntu/` is deleted or moved.""",
)

# --- section 10.2 step table: step 1 is half done; step 4 names its target -------------------

edit(
    "step 1 row",
    "| 1 | SMART test `sda`; restore-drill the CURRENT set | a drill passes on the current passphrase |",
    "| 1 | SMART test `sda` — **DONE 2026-09-23, PASSED** (note 10.2a). Restore-drill the CURRENT set — **still outstanding** | the drill passes on the current passphrase |",
)

edit(
    "step 4 row",
    "| 4 | Copy the 877 volumes to staging (≈203 GiB free required) | per-file hashes match the source |",
    "| 4 | Copy the 877 volumes to staging on **`nvme0n1p5` (`/`)** — **not** `sda` (note 10.2b); ≈203 GiB required | per-file hashes match the source |",
)

edit(
    "step 1 closing paragraph",
    """**Step 1 is first and is not optional.** Steps 4–7 are a bulk rewrite of the only local copy of
202.8 GiB, guarded by a disk whose health has never once been read. A rotation that loses the data it
was protecting has failed at the thing it was for.""",
    """**Step 1 is first, is not optional, and is currently HALF DONE**: the SMART half passed on
2026-09-23, the restore drill has not run, so step 2 is not yet unblocked. Steps 4–7 remain a bulk
rewrite of the only local copy of 202.8 GiB. A rotation that loses the data it was protecting has
failed at the thing it was for.

- **(10.2a)** **`sda` SMART, read 2026-09-23 — PASSED.** Evidence:
  `reports/smart/smart-xall_results-sda_2026-09-23_07:53:18.out`, produced by
  `util/ad-hoc/smart_checks_backup-sda.bash`. An **Extended offline** self-test completed without error
  at lifetime **28,938 h** against **28,941 h** at capture, so the scan is current and covered the
  surface. The header alone does **not** show this: `Self-test execution status: (0)` also means *"no
  self-test has ever been run"*, and only the self-test **log** disambiguates the two — read the log,
  never the status line. `Reallocated_Sector_Ct`, `Current_Pending_Sector`, `Offline_Uncorrectable`,
  `Reallocated_Event_Count` and `UDMA_CRC_Error_Count` are all **0**; the ATA error log and the Pending
  Defects log are both empty; every SATA Phy event counter is 0; temperature 39 °C with an
  under/over-limit count of 0/0. Age is the only soft spot and it reads better than the hours suggest —
  28,941 power-on hours (~3.3 years) but only **1,803 Head Flying Hours** and ~10.4 TB written in life.
  This **closes** the §12 / D-12a carried item "sda SMART never read".
- **(10.2b)** **Staging goes on `nvme0n1p5` (`/`), not on `sda`.** `sda1` has 3.1 TiB free and is the
  obvious-looking target, which is exactly the trap: it holds the sole local copy, so staging there puts
  the original and the re-encrypted copy in **one failure domain** for the whole of steps 4–7. The clean
  SMART report above does not change that — it lowers the probability, not the consequence, and the
  criterion the owner set is that access is *never* lost. `/` has 376 GiB free against the ~203 GiB
  needed, sits on a different physical device, is **ext4** so ownership and modes survive for D-14's
  read-only model, and is **outside the `/home/pcalnon` backup source**. `sdc3` (`/home`, 1.2 TiB free)
  satisfies the failure-domain test but fails the last one: staging there would sweep 203 GiB of
  ciphertext into the next fileset unless an exclusion were added first — the same class of mistake as
  S-7.""",
)


def main() -> int:
    if not DESIGN.is_file():
        print(f"FATAL: {DESIGN} not found (run from the repository root)", file=sys.stderr)
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
