#!/usr/bin/env python3
"""Consolidated development plan v1.15.2 -> v1.15.3: `[servers]` got the shared security patches through canopy 0.9.0.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2326 (the `[servers]` floors, where the claim started), #2349 / #2350 (the 0.11.3 cut and archive);
         util/ad-hoc/2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-10-26_plan_v1_7_21_servers_patch_path_corrected.py (the recurrence plan's matching revision)

Why
---
Since v1.15.0, §5 has listed `[all]` in R-ML-TOOLS's audience and described R-ML-SERVERS by the shared security
patches its floors carry. Neither holds. canopy 0.9.0 floors both patches with no extra marker, and `[servers]` has
required it since juniper-ml 0.11.0, so a `[servers]` or `[all]` install has carried them since 0.11.0. Session
"draft PRs" relayed the correction on 2026-10-26; every fact below was re-probed against PyPI's ``requires_dist`` and
juniper-cascor's ``CHANGELOG.md`` at ``v0.12.0`` before it was written. Every line stays within 512 characters, the
condition on which the owner approved v1.15.2 (2026-10-26), and the script refuses if any line is over.

Usage
-----
    python3 util/ad-hoc/2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py [--root DIR] [--check]

An edit already present is skipped, so a re-run is a no-op. An anchor found zero times or more than once, or a line
over 512 characters after the edits, refuses the whole run before anything is written. ``--check`` writes nothing and
exits 1 while an edit is pending.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"
MAX_LINE = 512

# Multi-line texts are bound to names here rather than written inside the REPLACEMENTS display: adjacent literals inside
# a list or tuple trip CodeQL's py/implicit-string-concatenation-in-list, whose unresolved thread blocks a merge.
_DATE_OLD = "juniper-ml 0.11.2's publish probed 2026-10-26)\n"
_DATE_NEW = "juniper-ml 0.11.2's publish probed 2026-10-26, and `[servers]`'s patch path corrected the same day)\n"

_STATUS_ANCHOR = "and the owner's ruling on ml#2330 with its fix, ml#2345 (XC-P12; §6 Group C). Like v1.15.0, no round checks it.\n"
_STATUS_ADD = (
    "  - v1.15.3 (2026-10-26) corrects how §5 says `[servers]` got the shared security patches: through canopy 0.9.0 since juniper-ml 0.11.0, with cascor 0.12.0 a second path from 0.11.2. "
    "So R-ML-TOOLS reached only `[tools]` installs without `[servers]`, and R-ML-SERVERS's security content is cascor 0.12.0's own fixes. It also points at juniper-ml 0.11.3, at the owner's gate (§5; XC-P12). Like v1.15.0, no round checks it.\n"
)

_FURTHER_P12_OLD = "`…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.20): the recurrence-client 0.3.1 cut and the owner's open items (§6 A1, A9)."
_FURTHER_P12_NEW = "`…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.21): juniper-ml 0.11.3's `pypi` gate (the owner's), the recurrence-client 0.3.1 cut and the owner's open items (§6 A1, A9)."

_TOOLS_AUDIENCE_OLD = "| `[tools]` and `[all]` users whose upgrade kept observability 0.4.0 or service-core 0.7.0 |"
_TOOLS_AUDIENCE_NEW = "| `[tools]` users without `[servers]` whose upgrade kept observability 0.4.0 or service-core 0.7.0 |"

_SERVERS_CONTENT_OLD = "(ml#2326), which floor the shared security patches. Rated as 0.11.1 (owner, 2026-10-25) |"
_SERVERS_CONTENT_NEW = "(ml#2326). Its security content is cascor 0.12.0's own fixes (note below). Rated as 0.11.1 (owner, 2026-10-25) |"
_SERVERS_AUDIENCE_OLD = "| `[servers]` and `[all]` users whose upgrade kept data 0.17.0 or cascor 0.11.0 |"
_SERVERS_AUDIENCE_NEW = "| `[servers]` and `[all]` users whose upgrade kept cascor 0.11.0 |"

_NOTES_ANCHOR = "its fix, ml#2333, merged on 2026-10-26 (`da5e8de3`) and ships in 0.11.3.\n"
_NOTES_ADD = (
    "  - 0.11.3 is cut: Release v0.11.3 at 10:20:47Z (tag at `a771a5b8`; archive ml#2350), and its publish run 40306687867 waits at the owner's `pypi` gate (2026-10-26; v1.15.3). Its records are session \"draft PRs\"'s.\n"
    "- **Corrected in v1.15.3: how `[servers]` got the shared security patches.** canopy 0.9.0, the only canopy at or above `[servers]`'s floor, floors `juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1,<0.8.0` with no extra marker, "
    "and `[servers]` has required it since 0.11.0. So `[servers]` and `[all]` have carried both patches since 0.11.0; cascor 0.12.0, whose floors are also unconditional, added a second path in 0.11.2.\n"
    "  - v1.15.0 to v1.15.2 listed `[all]` in R-ML-TOOLS's audience, and described R-ML-SERVERS by the shared patches its floors carry. An `[all]` install could not hold the unpatched pair from 0.11.0 on, so R-ML-TOOLS (0.11.1) reached only `[tools]` installs without `[servers]`.\n"
    "  - R-ML-SERVERS's security content is cascor 0.12.0's own fixes: cascor#659 (`APIKeyAuth` checks every key), #689 (a non-ASCII key is a 401, not a 500 that hands Sentry the key) and #710 (`FailedAuthThrottle`'s table stays bounded), all merged after cascor 0.11.0. "
    "data 0.17.1 floors the patches only under `[api]`, which 0.11.2's `[servers]` does not request.\n"
    "  - 0.11.2's notes repeat the error. The Priority line of `notes/releases/RELEASE_NOTES_v0.11.2.md` reads \"`[tools]` and `[all]` already floor both patches, since 0.11.1\", "
    "which under-warns any `[servers]` install that also has `[tools]` (`[all]` included) still on cascor 0.11.0.\n"
    "  - juniper-ml's `CHANGELOG.md` `[0.11.2]` (lines 223–224 on `main`, 2026-10-26) says they \"arrive through cascor 0.12.0\". An erratum to it, the notes and the Release v0.11.2 body is the owner's call.\n"
    "  - Source: session \"draft PRs\", which relayed the correction on 2026-10-26. Re-probed here against PyPI's `requires_dist` (juniper-canopy 0.9.0; juniper-ml 0.11.0 to 0.11.2; juniper-cascor 0.11.0 and 0.12.0; juniper-data 0.17.0 and 0.17.1) and juniper-cascor's `CHANGELOG.md` at `v0.12.0`.\n"
)

_VALIDATION_ANCHOR = "ml#2345's diff and `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py`.\n"
_VALIDATION_ADD = (
    "  - v1.15.3 is a correction (2026-10-26) of how §5 says `[servers]` got the shared security patches, with a pointer to juniper-ml 0.11.3 at its gate. No round checks it (owner ruling 2026-10-24); "
    "its facts cite PyPI's `requires_dist`, juniper-cascor's `CHANGELOG.md` at `v0.12.0`, Release v0.11.3, run 40306687867 and `util/ad-hoc/2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py`.\n"
)

_SCRIPTS_OLD = "`2026-10-25_consolidated_plan_v1_15_1_session_record.py`; and with v1.15.2's, `2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py`;\n"
_SCRIPTS_NEW = (
    "`2026-10-25_consolidated_plan_v1_15_1_session_record.py`; with v1.15.2's, `2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py`; "
    "and with v1.15.3's, `2026-10-26_consolidated_plan_v1_15_3_servers_patch_path_corrected.py`;\n"
)

_MEMORY_ANCHOR = "  - by session `53dbcc4b` (2026-10-26), with v1.15.2: the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.2), and `project_recurrence_equities_p0_arc_2026-10-04.md` and its line in `MEMORY.md`.\n"
_MEMORY_ADD = "  - by session `53dbcc4b` (2026-10-26), with v1.15.3: `project_recurrence_equities_p0_arc_2026-10-04.md` and its line in `MEMORY.md`.\n"

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.2\n", "- **Version**: 1.15.3\n"),
    (_STATUS_ANCHOR, _STATUS_ANCHOR + _STATUS_ADD),
    (_FURTHER_P12_OLD, _FURTHER_P12_NEW),
    (_TOOLS_AUDIENCE_OLD, _TOOLS_AUDIENCE_NEW),
    (_SERVERS_CONTENT_OLD, _SERVERS_CONTENT_NEW),
    (_SERVERS_AUDIENCE_OLD, _SERVERS_AUDIENCE_NEW),
    (_NOTES_ANCHOR, _NOTES_ANCHOR + _NOTES_ADD),
    (_VALIDATION_ANCHOR, _VALIDATION_ANCHOR + _VALIDATION_ADD),
    (_SCRIPTS_OLD, _SCRIPTS_NEW),
    (_MEMORY_ANCHOR, _MEMORY_ANCHOR + _MEMORY_ADD),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=_REPO)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    path = args.root / PLAN
    text = path.read_text(encoding="utf-8")
    pending = refused = 0
    for old, new in REPLACEMENTS:
        site = old.strip()[:72]
        if new in text and text.count(old) <= text.count(new):
            # ``new`` may contain ``old`` (an insertion after an anchor); applied means each old sits inside a new.
            print(f"  = {site}... already applied")
            continue
        if text.count(old) != 1:
            print(f"  ! {site}... REFUSED: found {text.count(old)} times, expected 1")
            refused += 1
            continue
        text = text.replace(old, new, 1)
        pending += 1
        print(f"  ~ {site}... {'pending' if args.check else 'applied now'}")

    long_lines = [(n, len(line)) for n, line in enumerate(text.split("\n"), 1) if len(line) > MAX_LINE]
    for n, width in long_lines:
        print(f"  ! line {n} is {width} characters, over {MAX_LINE}")
    if refused or long_lines:
        print(f"REFUSED: {refused} anchor(s), {len(long_lines)} long line(s); nothing written", file=sys.stderr)
        return 1
    if args.check:
        return 1 if pending else 0
    if pending:
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
