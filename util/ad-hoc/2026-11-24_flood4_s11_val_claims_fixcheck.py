#!/usr/bin/env python3
"""
Check that each proposed old->new fix for the flood-4 record update applies exactly once, in order (validator V1).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11, validator V1 claims lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (proof that the claims-lens findings' fixes are mechanically applicable)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (the drafted copy);
         tmp/flood4/session11/record/val_claims/findings.md (the findings these fixes belong to)

What it does
------------
Reads a JSON list of fixes (``--fixes``: id, file = "record" | "changelog", old, new) and the two target files
(``--record``, ``--changelog``). For each fix, in list order, it counts ``old`` in the current text of its target
(the text as changed by the fixes before it): it must occur exactly once. Prints one row per fix (OK / COUNT n).
With ``--out-dir`` it also writes both texts with every applicable fix applied, as a preview; it never writes the
targets themselves.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_val_claims_fixcheck.py --fixes <fixes.json> --record <record.md>
        --changelog <changelog_entry.md> [--out-dir <dir>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--fixes", required=True)
    ap.add_argument("--record", required=True)
    ap.add_argument("--changelog", required=True)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()
    with open(args.fixes, encoding="utf-8") as fh:
        fixes = json.load(fh)
    texts = {"record": Path(args.record).read_text(encoding="utf-8"), "changelog": Path(args.changelog).read_text(encoding="utf-8")}
    bad = 0
    for fx in fixes:
        text = texts[fx["file"]]
        n = text.count(fx["old"])
        if n == 1:
            texts[fx["file"]] = text.replace(fx["old"], fx["new"], 1)
            print(f"OK       {fx['id']:<5} {fx['file']}")
        else:
            bad += 1
            print(f"COUNT {n}  {fx['id']:<5} {fx['file']}  old={fx['old'][:80]!r}")
    if args.out_dir:
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "record_with_fixes.md").write_text(texts["record"], encoding="utf-8")
        (out / "changelog_entry_with_fixes.md").write_text(texts["changelog"], encoding="utf-8")
    print(f"summary: {len(fixes) - bad} applicable, {bad} not", file=sys.stderr)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
