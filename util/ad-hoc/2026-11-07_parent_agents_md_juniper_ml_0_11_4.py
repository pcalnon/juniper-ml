#!/usr/bin/env python3
"""Edit the parent ``Juniper/AGENTS.md`` RELEASED paragraph for juniper-ml 0.11.4 and juniper-recurrence 0.8.1.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (an owner-approved edit of an UNVERSIONED file)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (v1.15.14 records the edit);
         util/ad-hoc/2026-11-07_parent_agents_released_paragraph_reprobe.py (the PyPI re-read the new date rests on);
         util/ad-hoc/2026-11-07_verify_juniper_ml_0_11_4_published.py (the publish check)

Why this exists
---------------
The parent ``Juniper/AGENTS.md`` is in no git repository, so an edit to it has no PR, no CI and no history. The
owner approved this one on 2026-11-07, in session ``a02ac3a2``'s question, with a backup taken first. Its
"What has moved since" list said juniper-ml 0.11.3 was the latest on PyPI and stopped juniper-recurrence at
0.8.0. A re-read of all eleven packages the paragraph names (2026-11-07) found exactly those two moved: recurrence
0.8.1 (2026-11-06) and juniper-ml 0.11.4 (2026-11-07). So the re-probe date may move too.

Safety
------
- The input must have the sha256 it had when the edit was approved (``EXPECTED_SHA256``); any other content is
  refused, so an edit another session made in between is never overwritten.
- Every anchor must occur exactly once; otherwise nothing is written.
- Before writing, the input is copied to ``BACKUP_DIR`` as ``AGENTS.md.before-juniper-ml-0-11-4-edit``; after, the
  output as ``AGENTS.md.after-juniper-ml-0-11-4-edit``. An existing backup that differs is refused.

Usage
-----
    python3 -I util/ad-hoc/2026-11-07_parent_agents_md_juniper_ml_0_11_4.py --check   # writes nothing; 1 while pending
    python3 -I util/ad-hoc/2026-11-07_parent_agents_md_juniper_ml_0_11_4.py           # backs up, then edits
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import sys
from pathlib import Path

_ECOSYSTEM = Path.home() / "Development" / "python" / "Juniper"
TARGET = _ECOSYSTEM / "AGENTS.md"
# The juniper-ml primary checkout's repo temp root (gitignored), where the 2026-10-29 and 2026-11-01 backups live too.
BACKUP_DIR = _ECOSYSTEM / "juniper-ml" / "tmp" / "2026-11-07-parent-agents-md-backup"
BEFORE_NAME = "AGENTS.md.before-juniper-ml-0-11-4-edit"
AFTER_NAME = "AGENTS.md.after-juniper-ml-0-11-4-edit"
EXPECTED_SHA256 = "29e375ff57f1464e9c255a33251c047a2c95b27c3c3c9f5d5ecb222cbfe2e873"

_DATE_OLD = "**Last Updated**: 2026-11-01\n"
_DATE_NEW = "**Last Updated**: 2026-11-07\n"

_PROBE_OLD = "    **What has moved since (re-probed against PyPI on 2026-10-29 UTC):**\n"
_PROBE_NEW = "    **What has moved since (re-probed against PyPI on 2026-11-07 UTC):**\n"

_RECURRENCE_ANCHOR = "        `juniper-observability>=0.4.1`).\n    - **juniper-canopy 0.9.0**"
_RECURRENCE_NEW = (
    "        `juniper-observability>=0.4.1`).\n"
    "      - **0.8.1** (2026-11-06 09:35Z, publish run 41935261358) floors\n"
    "        `juniper-model-core[crossval]>=0.3.0,<0.4.0` (juniper-recurrence#229). 0.8.0's\n"
    "        `_folds.build_folds` passes `groups=` to `walk_forward_folds` on every\n"
    "        `POST /v1/crossval`, which model-core has only from 0.3.0, while 0.8.0 declared\n"
    "        `>=0.2.0`: an environment holding model-core 0.2.0 passed `pip check` and answered\n"
    "        500 on every crossval request.\n"
    "    - **juniper-canopy 0.9.0**"
)

_ML_OLD = (
    "    - **The meta-package: juniper-ml 0.11.3** (2026-10-26 17:48Z, publish run\n"
    "      40306687867; Release `v0.11.3`, tag at juniper-ml `a771a5b8`) is the latest on PyPI.\n"
    "      It is a patch with no security content, and carries juniper-ml#2062's fix (the last\n"
    "      bullet below). It followed 0.11.2 (2026-10-26 08:38Z, publish run 40247789317),\n"
    "      0.11.1 (2026-10-25 18:03Z), 0.11.0 (2026-10-21) and 0.10.0 (2026-09-23, publish run\n"
    "      35879664979).\n"
)
_ML_NEW = (
    "    - **The meta-package: juniper-ml 0.11.4** (2026-11-07 22:59Z, publish run\n"
    "      42230617125; Release `v0.11.4`, tag at juniper-ml `957f0e94`) is the latest on PyPI.\n"
    "      It is a patch with no security content: `[recurrence]` floors\n"
    "      `juniper-recurrence>=0.8.1` (juniper-ml#2473), so `pip install -U juniper-ml[recurrence]`\n"
    "      moves an environment off recurrence 0.8.0, and with it off model-core 0.2.0. It\n"
    "      followed 0.11.3 (2026-10-26 17:48Z, publish run 40306687867; tag at `a771a5b8`),\n"
    "      which carries juniper-ml#2062's fix (the last bullet below), 0.11.2 (2026-10-26\n"
    "      08:38Z, publish run 40247789317), 0.11.1 (2026-10-25 18:03Z), 0.11.0 (2026-10-21)\n"
    "      and 0.10.0 (2026-09-23, publish run 35879664979).\n"
)

_EXTRA_OLD = (
    "      - `[recurrence]` is `juniper-recurrence>=0.8.0,<0.9.0` and\n"
    "        `juniper-recurrence-model>=0.6.0,<0.7.0`. 0.10.0 capped them at `<0.6.0` and\n"
    "        `<0.4.0`, which held `[all]` at recurrence 0.5.0.\n"
)
_EXTRA_NEW = (
    "      - `[recurrence]` is `juniper-recurrence>=0.8.1,<0.9.0` (since 0.11.4; 0.11.0 to\n"
    "        0.11.3 floor `>=0.8.0`) and `juniper-recurrence-model>=0.6.0,<0.7.0`. 0.10.0\n"
    "        capped them at `<0.6.0` and `<0.4.0`, which held `[all]` at recurrence 0.5.0.\n"
)

#: (old, new): ``old`` must occur exactly once in the input.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    (_PROBE_OLD, _PROBE_NEW),
    (_RECURRENCE_ANCHOR, _RECURRENCE_NEW),
    (_ML_OLD, _ML_NEW),
    (_EXTRA_OLD, _EXTRA_NEW),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 while the edit is pending")
    args = ap.parse_args()

    raw = TARGET.read_bytes()
    after_backup = BACKUP_DIR / AFTER_NAME
    if after_backup.exists() and raw == after_backup.read_bytes():
        print(f"= {TARGET} already carries the edit (sha256 {sha256(raw)} = {AFTER_NAME})")
        return 0
    if sha256(raw) != EXPECTED_SHA256:
        print(f"REFUSED: {TARGET} has sha256 {sha256(raw)}, not the approved input {EXPECTED_SHA256}; nothing written", file=sys.stderr)
        return 1
    text = raw.decode("utf-8")
    for old, new in REPLACEMENTS:
        count = text.count(old)
        if count != 1:
            print(f"REFUSED: anchor found {count} times, expected 1: {old.strip()[:72]!r}; nothing written", file=sys.stderr)
            return 1
        text = text.replace(old, new, 1)
    out = text.encode("utf-8")
    diff = difflib.unified_diff(raw.decode("utf-8").splitlines(keepends=True), text.splitlines(keepends=True), "AGENTS.md (before)", "AGENTS.md (after)")
    sys.stdout.writelines(diff)
    if args.check:
        print(f"pending: {len(REPLACEMENTS)} edits; input sha256 {sha256(raw)}, output would be {sha256(out)}")
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    before_backup = BACKUP_DIR / BEFORE_NAME
    if before_backup.exists() and before_backup.read_bytes() != raw:
        print(f"REFUSED: {before_backup} exists and differs from the input; nothing written", file=sys.stderr)
        return 1
    before_backup.write_bytes(raw)
    TARGET.write_bytes(out)
    after_backup.write_bytes(out)
    print(f"OK {TARGET}: sha256 {sha256(raw)} -> {sha256(out)}; backups in {BACKUP_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
