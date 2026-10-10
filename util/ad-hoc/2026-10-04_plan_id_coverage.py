#!/usr/bin/env python3
"""
Check that every extraction-report item ID is placed in a plan, and list IDs dropped between two plan versions.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-04
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (Appendix A)

IDs look like ``P<n>-<NN>`` (n = 1..12) or ``P<n>-R<N>``/``P<n>-R<NN>``. Ranges written ``P12-10..P12-19`` / ``P12-10..19`` and
slash lists written ``P7-06/07/08`` are expanded before comparison, so a range placement counts as placing every
ID in it. Extraction-report IDs are read from the first column of their item tables (``| P3-07 |``).

Usage
-----
    python3 util/ad-hoc/2026-10-04_plan_id_coverage.py OLD_PLAN NEW_PLAN 'reports/<dir>/extraction-*.md'
Exit 0 when nothing is dropped and nothing is missing; 1 otherwise.
"""
import glob
import hashlib
import re
import sys
from pathlib import Path

P = r"P(?:1[0-2]|[1-9])"


def ids(text: str) -> set:
    # R-IDs added by validation can have one digit (P2-R8); item IDs always have two (round 8's reconciliation)
    out = set(re.findall(rf"\b{P}-(?:R\d{{1,2}}|\d{{2}})\b", text))
    for m in re.finditer(rf"\b({P})-(\d{{2}})\.\.(?:{P}-)?(\d{{2}})\b", text):
        p, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        out |= {f"{p}-{n:02d}" for n in range(a, b + 1)}
    for m in re.finditer(rf"\b({P})-(\d{{2}})((?:/\d{{2}})+)", text):
        p = m.group(1)
        out |= {f"{p}-{x}" for x in [m.group(2)] + m.group(3).strip("/").split("/")}
    return out


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    old_path, new_path, rep_glob = sys.argv[1:4]
    old, new = Path(old_path).read_text(), Path(new_path).read_text()
    print("old sha256", hashlib.sha256(old.encode()).hexdigest()[:16], "| new sha256", hashlib.sha256(new.encode()).hexdigest()[:16])
    io, inew = ids(old), ids(new)
    dropped = sorted(io - inew)
    ex = set()
    for f in glob.glob(rep_glob):
        ex |= set(re.findall(rf"\|\s*({P}-\d{{2}})\b", Path(f).read_text()))
    missing = sorted(ex - inew, key=lambda s: (int(s[1:].split("-")[0]), s))
    print("old ids", len(io), "| new ids", len(inew), "| dropped:", dropped)
    print("extraction ids", len(ex), "| missing from new:", missing)
    return 0 if not dropped and not missing else 1


if __name__ == "__main__":
    sys.exit(main())
