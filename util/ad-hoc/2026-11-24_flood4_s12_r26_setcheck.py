#!/usr/bin/env python3
"""Check session 12's fixed ruling-26 sets against both V26 lenses' own fixed copies (flood-4 session 12).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (the fix pass before ruling 26's six PRs land; tmp/flood4/session12/r26/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_flood4_s12_r26_fixpass.py (builds the sets this checks);
    util/ad-hoc/2026-11-24_flood4_s11_v26_claims_fixes.py (the claims lens's preview) and
    util/ad-hoc/2026-11-24_flood4_s11_v26_code_propose.py (the code lens's proposed copies)

Checks, for the six sets under --sets:
  1. every file of the claims lens's preview under final/ (CHANGELOGs, juniper-data's CICD_REFERENCE.md) equals the
     set's copy byte for byte;
  2. for each of the five ports, the set's test file equals the code lens's proposed copy (C1 applied, and proven by
     that lens), and the set's workflow equals session 11's frozen workflow (the fix pass does not touch it);
  3. each set's texts differ from the claims preview only by the lines printed (a unified diff, for review).
Reads only; writes nothing. Exit 0 when checks 1 and 2 pass.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r26_setcheck.py --sets DIR --s11 DIR
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

PORTS = ["juniper-data", "juniper-cascor", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker"]
WORKFLOW = ".github/workflows/lockfile-update.yml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sets", type=Path, required=True)
    parser.add_argument("--s11", type=Path, required=True)
    args = parser.parse_args()
    preview = args.s11 / "val_claims" / "preview"
    ok = True

    print("== 1. claims preview final/ files")
    for path in sorted(p for p in preview.rglob("*") if p.is_file() and "final" in p.relative_to(preview).parts):
        rel = path.relative_to(preview)
        same = (args.sets / rel).read_bytes() == path.read_bytes()
        ok &= same
        print(f"  {'SAME' if same else 'DIFF'} {rel}")

    print("== 2. C1 test files and workflows")
    for repo in PORTS:
        rels = [line.strip() for line in (args.s11 / repo / "paths.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
        test = next(rel for rel in rels if rel.endswith(".py"))
        proposed = args.s11 / "val_code" / repo / "proposed" / "final" / test
        same_test = (args.sets / repo / "final" / test).read_bytes() == proposed.read_bytes()
        same_wf = (args.sets / repo / "final" / WORKFLOW).read_bytes() == (args.s11 / repo / "final" / WORKFLOW).read_bytes()
        ok &= same_test and same_wf
        print(f"  {repo:22} test {'SAME' if same_test else 'DIFF'} as the code lens's proposed copy; workflow {'SAME' if same_wf else 'DIFF'} as session 11's")

    print("== 3. texts vs the claims preview (the lines that differ)")
    for repo in [*PORTS, "juniper-canopy"]:
        for name in ("pr_body.md", "commit_body.txt"):
            base = preview / repo / "texts" / name
            if not base.exists():
                base = args.s11 / repo / "texts" / name
            old = base.read_text(encoding="utf-8").splitlines()
            new = (args.sets / repo / "texts" / name).read_text(encoding="utf-8").splitlines()
            lines = [d for d in difflib.unified_diff(old, new, lineterm="", n=0) if d[:1] in "+-" and d[:3] not in ("+++", "---")]
            print(f"  {repo}/{name} (against {'the preview' if 'preview' in base.parts else 'the builder copy'}):")
            for line in lines:
                print(f"    {line[:220]}")
    print("RESULT: " + ("OK" if ok else "MISMATCH ABOVE"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
