#!/usr/bin/env python3
"""Plan v1.7.21: `[servers]` has carried the shared security patches since juniper-ml 0.11.0, through canopy 0.9.0.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.20 -> v1.7.21);
         util/ad-hoc/2026-10-26_plan_v1_7_20_juniper_ml_0_11_2_published.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py (the consolidated plan's matching revision)

Why
---
v1.7.17 wrote that a `[servers]` install "gets the patches through cascor 0.12.0, whose floors are unconditional",
which reads as the only path. Session "draft PRs", which started the claim in juniper-ml#2326, relayed the
correction on 2026-10-26, and it was re-probed here against PyPI's ``requires_dist`` before it was written: canopy
0.9.0 floors both patches with no extra marker, and `[servers]` has required it since 0.11.0. The sentence stays where
it stands, in the Status line, the Progress block and the 1.7.17 Change Log row, each followed by an annotation.

Usage
-----
    python3 util/ad-hoc/2026-10-26_plan_v1_7_21_servers_patch_path_corrected.py [--plan PATH] [--check]

``--plan`` points the script at a copy of the plan; the default is the repo's own copy. Every single-site anchor must
match exactly once, and v1.7.17's sentence exactly three times, or the script refuses and writes nothing. ``--check``
reports what is applied / pending without writing, and exits 1 while an edit is owed.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_HEADLINE = "`[servers]`'s patch path corrected; juniper-ml 0.11.3 at the `pypi` gate"

RECORD = (
    "v1.7.17 said a `[servers]` install \"gets the patches through cascor 0.12.0\", as if that were the only path. It "
    "is not: juniper-canopy 0.9.0, the only canopy release at or above `[servers]`'s floor, floors "
    "`juniper-observability>=0.4.1,<0.5.0` and `juniper-service-core>=0.7.1,<0.8.0` with no extra marker, and "
    "`[servers]` has required `juniper-canopy>=0.9.0` since juniper-ml 0.11.0. So `[servers]` and `[all]` installs "
    "have carried both shared patches since 0.11.0, and cascor 0.12.0 added a second path in 0.11.2 (cascor 0.11.0 "
    "floors only `>=0.4.0` and `>=0.5.0,<0.8.0`). 0.11.2's security content for `[servers]` and `[all]` is therefore "
    "cascor 0.12.0's own fixes, among them juniper-cascor#659 (`APIKeyAuth` checks every configured key), #689 (a "
    "non-ASCII API key is a 401, not a 500 that hands Sentry the real key) and #710 (`FailedAuthThrottle.check()` no "
    "longer inserts every unseen source IP), all merged after cascor 0.11.0 and all in juniper-cascor's `CHANGELOG.md` "
    "`[0.12.0]`. "
    "Re-probed against PyPI's `requires_dist` for juniper-canopy 0.9.0, juniper-ml 0.11.0-0.11.2, juniper-cascor "
    "0.11.0 and 0.12.0 and juniper-data 0.17.0 and 0.17.1 on 2026-10-26; the correction came from session \"draft "
    "PRs\", which started the claim in juniper-ml#2326, and v1.7.17's sentence is annotated where it stands. 0.11.2's "
    "notes repeat it: `notes/releases/RELEASE_NOTES_v0.11.2.md`'s Priority line says \"`[tools]` and `[all]` already "
    "floor both patches, since 0.11.1\", which under-warns any `[servers]` install that also has `[tools]` (`[all]` "
    "included) still on cascor 0.11.0, and juniper-ml's `CHANGELOG.md` `[0.11.2]` entry (lines 223-224 on `main`, "
    "2026-10-26) says the patches \"arrive through cascor 0.12.0\". An erratum to those two and the Release v0.11.2 "
    "body is the owner's call, raised by that session. juniper-ml 0.11.3, which carries "
    "juniper-ml#2333 (#2062's fix), is cut: Release `v0.11.3` at 10:20:47Z (tag at `a771a5b8`; archive juniper-ml#2350, "
    "`8b2221d3`), and publish run 40306687867 waits at the owner's `pypi` gate; its records are that session's. "
    "`JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` carries the same correction (v1.15.3)"
)

#: v1.7.17's sentence, in the Status line, the Progress block and the 1.7.17 Change Log row; each copy is annotated.
V1717_SENTENCE = (
    "`[servers]` installs bare `juniper-data`, so a `[servers]` install gets the patches through cascor 0.12.0, whose "
    "floors are unconditional."
)
V1717_NOTE = (
    " *(Corrected in v1.7.21: not the only path. juniper-canopy 0.9.0 floors both patches with no extra marker, and "
    "`[servers]` has required it since juniper-ml 0.11.0.)*"
)
_V1717_COPIES = 3

_STATUS_ANCHOR = "pins both bounds in CI). The v1.4.0 plan edits follow that record"

NEXT_HEAD_OLD = (
    "  - **Next**: juniper-ml#2062's fix (`[servers]` installs no client, as 0.11.2's still does), juniper-ml#2333, "
    "merged as `da5e8de3` (2026-10-26 09:10Z); it ships in juniper-ml 0.11.3 (owner ruling 2026-10-25), whose `pypi` "
    "gate is the owner's. "
)
NEXT_HEAD_NEW = (
    "  - **Next**: juniper-ml 0.11.3, which carries juniper-ml#2062's fix (juniper-ml#2333, `da5e8de3`), waits at the "
    "owner's `pypi` gate (publish run 40306687867; re-runnable until 2026-11-25 10:20Z, and GitHub cancels it on "
    "2026-11-30 10:20Z); its records are session \"draft PRs\"'s. Whether 0.11.2's notes take an erratum for the patch "
    "path is the owner's call (v1.7.21). "
)
#: The unchanged tail of the Next bullet, asserted so the head edit cannot land on a rewritten bullet.
_NEXT_TAIL = "The juniper-recurrence-client 0.3.1 release (owner's cut) carries the embargo fix."

_ROW_ANCHOR_START = "| 2026-10-26 | 1.7.20 | **juniper-ml 0.11.2 published, juniper-ml#2330 ruled**:"
_ROW_START = "| 2026-10-26 | 1.7.21 | "
_ROW_UPDATED = (
    "Updated: Status line (this record; v1.7.17's sentence annotated), the Progress block (a session bullet before "
    "**Next**; the head of **Next** rewritten, its tail unchanged; v1.7.17's sentence annotated) and the 1.7.17 row "
    "(v1.7.17's sentence annotated). | Paul Calnon |"
)


def edits() -> list[tuple[str, str]]:
    bullet = f"  - **{_HEADLINE} (Linux host, 2026-10-26)**: {RECORD}.\n"
    return [
        ("- **Version**: 1.7.20", "- **Version**: 1.7.21"),
        (_STATUS_ANCHOR, _STATUS_ANCHOR.replace("CI). The v1.4.0", f"CI); **{_HEADLINE}** (v1.7.21: {RECORD}). The v1.4.0")),
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

    # v1.7.17's sentence: every copy annotated, or none. The annotated form contains the bare one, so count both.
    annotated = text.count(V1717_SENTENCE + V1717_NOTE)
    bare = text.count(V1717_SENTENCE) - annotated
    if annotated == _V1717_COPIES and bare == 0:
        print(f"  = already applied: v1.7.17's sentence annotated {annotated} times")
    elif annotated == 0 and bare == _V1717_COPIES:
        owed += 1
        text = text.replace(V1717_SENTENCE, V1717_SENTENCE + V1717_NOTE)
        print(f"  {'~ WOULD annotate' if args.check else '+ annotated'} v1.7.17's sentence {bare} times")
    else:
        raise SystemExit(f"ERROR: expected v1.7.17's sentence {_V1717_COPIES} times, all bare or all annotated; found {bare} bare and {annotated} annotated")

    if _ROW_START in text:
        print("  = revision row already present")
    else:
        starts = [m.start() for m in re.finditer(re.escape(_ROW_ANCHOR_START), text)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.20 revision row, found {len(starts)}")
        end = text.find("\n", starts[0])
        end = len(text) if end < 0 else end
        owed += 1
        text = text[:end] + "\n" + row() + text[end:]
        print(f"  {'~ WOULD add' if args.check else '+ added'} the revision row after v1.7.20")

    if args.check:
        print(f"--check: {owed} edit(s) owed; nothing written")
        return 1 if owed else 0
    if text != original:
        args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
