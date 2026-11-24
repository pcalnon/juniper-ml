#!/usr/bin/env python3
"""
Correct the round-38 filing's dates: the findings are 2026-09-08, the closes and the filing
are 2026-09-09 (the three PRs merged on the 9th).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-09
Status: ad-hoc — one-off (companion to util/ad-hoc/register_round38_file.py, which was written on
        the 8th and dated its own closes 2026-09-08; the PRs merged 2026-09-09T17:14Z / 17:57Z / 19:25Z)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/register_round38_file.py;
         HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md

A close date is the date the fix LANDED, not the date the defect was found or the row drafted --
otherwise the register's chronology disagrees with `gh pr view --json mergedAt`, which is the only
receipt a later reader can check.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = ROOT / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

EDITS = [
    ("**Last Updated**: 2026-09-08\n", "**Last Updated**: 2026-09-09\n"),
    (
        "**Post-primer rows** ([§4.9](#49-filed-after-the-primer), filed 2026-09-08 from the round-37/38 handoff validation, not counted in the 96): fourteen filed, of which (2026-09-08) `APD-DATA-037`",
        "**Post-primer rows** ([§4.9](#49-filed-after-the-primer), filed 2026-09-09 from the 2026-09-08 round-37/38 handoff validation, not counted in the 96): fourteen filed, of which (2026-09-09) `APD-DATA-037`",
    ),
    (
        "> *(2026-09-08: the post-primer rows filed in [§4.9](#49-filed-after-the-primer) carry their own",
        "> *(2026-09-09: the post-primer rows filed in [§4.9](#49-filed-after-the-primer) carry their own",
    ),
    (
        "the four-significant-figure values this note carried until 2026-09-08 were one run on one machine and are withdrawn",
        "the four-significant-figure values this note carried until 2026-09-09 were one run on one machine and are withdrawn",
    ),
]


def main() -> int:
    text = REG.read_text()
    for old, new in EDITS:
        n = text.count(old)
        if n != 1:
            sys.exit(f"FAIL: expected 1 match, found {n} for:\n---\n{old[:200]}\n---")
        text = text.replace(old, new)
        print(f"edited: {old.splitlines()[0][:70]!r}")
    REG.write_text(text)

    sys.path.insert(0, str(HERE))
    from register_open_set import format_report, parse_register  # noqa: E402
    from register_status_crosscheck import crosscheck  # noqa: E402

    seen, fixed = parse_register(text)
    print("open-set:", format_report(seen, fixed).splitlines()[0])
    return crosscheck(text)


if __name__ == "__main__":
    raise SystemExit(main())
