#!/usr/bin/env python3
"""Plan v1.7.22: juniper-ml 0.11.3 is published, so the head of **Next** no longer names its `pypi` gate.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.21 -> v1.7.22);
         util/ad-hoc/2026-10-26_plan_v1_7_21_servers_patch_path_corrected.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-10-26_consolidated_plan_v1_15_4_juniper_ml_0_11_3_published.py (the consolidated plan's matching revision)

Why
---
v1.7.21's **Next** opened with juniper-ml 0.11.3 waiting at the owner's `pypi` gate. The owner approved that gate on
2026-10-26 and PyPI serves 0.11.3 from 17:48Z, so the head of **Next** is rewritten. v1.7.21's records of the gate stay
where they stand: they were true when written. The publish was probed here, against PyPI's and TestPyPI's version JSON
and the run's jobs and approvals; the two peer results the record cites are marked as relayed.

Usage
-----
    python3 util/ad-hoc/2026-10-26_plan_v1_7_22_juniper_ml_0_11_3_published.py [--plan PATH] [--check]

``--plan`` points the script at a copy of the plan; the default is the repo's own copy. Every anchor must match exactly
once, or the script refuses and writes nothing. ``--check`` reports what is applied / pending without writing, and
exits 1 while an edit is owed.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_HEADLINE = "juniper-ml 0.11.3 published"

RECORD = (
    "the owner approved the `pypi` gate of publish run 40306687867 on 2026-10-26, and `Publish to PyPI` succeeded "
    "(17:47:43Z-17:48:12Z). `https://pypi.org/pypi/juniper-ml/0.11.3/json` serves the wheel (17:48:05Z) and the sdist "
    "(17:48:07Z), each with the sha256 TestPyPI took at 10:21Z, and the index's latest version is 0.11.3. Its three "
    "`[servers]` lines are `juniper-canopy[juniper-cascor,juniper-data]>=0.9.0`, `juniper-cascor[api,juniper-data]>=0.12.0` "
    "and `juniper-data[api]>=0.17.1`, so juniper-ml#2062's fix (juniper-ml#2333) ships, and data 0.17.1's `[api]` floors "
    "on the shared patches now reach `[servers]` too. Session \"draft PRs\", which keeps 0.11.3's records, ran "
    "`util/ad-hoc/2026-10-25_verify_servers_extras_ml2062.bash` against the published `juniper-ml[servers]==0.11.3`: "
    "JD-8, CC-2 and CC-3 pass, CP-1 imports canopy's `backend.service_backend`, and `pip check` is clean (of 39 checks, "
    "26 PASS, 13 SKIP and 0 FAIL; the 0.11.2 control, on the same server releases, was 18 PASS and 21 SKIP; relayed, not "
    "re-run here). The turing session \"recurrence equities 0\" [4156c8] reports that juniper-ml#2345's post-merge "
    "re-check passed on `main` `31b34c39` (relayed): juniper-ml's `CHANGELOG.md` holds the juniper-ml#2330 entry once, "
    "at line 66 under `[0.11.3]`, `### Fixed` (re-read here), and that thread ends with nothing carried forward, by the "
    "owner's choice. An erratum to 0.11.2's notes (`notes/releases/RELEASE_NOTES_v0.11.2.md`, juniper-ml's "
    "`CHANGELOG.md` `[0.11.2]` and the Release v0.11.2 body) stays the owner's call (v1.7.21); the Release body is "
    "unedited since 2026-10-26 00:08:22Z. "
    "`JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` records the same publish (v1.15.4)"
)

_STATUS_ANCHOR = "carries the same correction (v1.15.3)). The v1.4.0 plan edits follow that record"

NEXT_HEAD_OLD = (
    "  - **Next**: juniper-ml 0.11.3, which carries juniper-ml#2062's fix (juniper-ml#2333, `da5e8de3`), waits at the "
    "owner's `pypi` gate (publish run 40306687867; re-runnable until 2026-11-25 10:20Z, and GitHub cancels it on "
    "2026-11-30 10:20Z); its records are session \"draft PRs\"'s. Whether 0.11.2's notes take an erratum for the patch "
    "path is the owner's call (v1.7.21). "
)
NEXT_HEAD_NEW = "  - **Next**: whether 0.11.2's notes take an erratum for the patch path is the owner's call (v1.7.21). "
#: The unchanged tail of the Next bullet, asserted so the head edit cannot land on a rewritten bullet.
_NEXT_TAIL = "The juniper-recurrence-client 0.3.1 release (owner's cut) carries the embargo fix."

_ROW_ANCHOR_START = "| 2026-10-26 | 1.7.21 | **`[servers]`'s patch path corrected; juniper-ml 0.11.3 at the `pypi` gate**:"
_ROW_START = "| 2026-10-26 | 1.7.22 | "
_ROW_UPDATED = (
    "Updated: Status line (this record) and the Progress block (a session bullet before **Next**; the head of **Next** "
    "rewritten, its tail unchanged). | Paul Calnon |"
)


def edits() -> list[tuple[str, str]]:
    bullet = f"  - **{_HEADLINE} (Linux host, 2026-10-26)**: {RECORD}.\n"
    status_new = _STATUS_ANCHOR.replace("(v1.15.3)). The v1.4.0", f"(v1.15.3)); **{_HEADLINE}** (v1.7.22: {RECORD}). The v1.4.0")
    return [
        ("- **Version**: 1.7.21", "- **Version**: 1.7.22"),
        (_STATUS_ANCHOR, status_new),
        # Progress block: the session bullet before the Next bullet, and the head of the Next bullet rewritten.
        (NEXT_HEAD_OLD + _NEXT_TAIL, bullet + NEXT_HEAD_NEW + _NEXT_TAIL),
    ]


def row() -> str:
    return f"{_ROW_START}**{_HEADLINE}**: {RECORD}. {_ROW_UPDATED}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: the repo's own copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 while an edit is owed)")
    args = ap.parse_args()

    text = args.plan.read_text(encoding="utf-8")
    original = text
    owed = 0
    for old, new in edits():
        if new in text and old not in text:
            print(f"  = already applied: {new[:80]!r}")
            continue
        if text.count(old) != 1:
            raise SystemExit(f"ERROR: expected exactly one occurrence of {old[:90]!r}, found {text.count(old)}")
        owed += 1
        print(f"  {'~ WOULD apply' if args.check else '+ applied'}: {old[:80]!r}")
        text = text.replace(old, new, 1)

    if _ROW_START in text:
        print("  = revision row already present")
    else:
        starts = [m.start() for m in re.finditer(re.escape(_ROW_ANCHOR_START), text)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.21 revision row, found {len(starts)}")
        end = text.find("\n", starts[0])
        end = len(text) if end < 0 else end
        owed += 1
        text = text[:end] + "\n" + row() + text[end:]
        print(f"  {'~ WOULD add' if args.check else '+ added'} the revision row after v1.7.21")

    if args.check:
        print(f"--check: {owed} edit(s) owed; nothing written")
        return 1 if owed else 0
    if text != original:
        args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
