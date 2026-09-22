#!/usr/bin/env python3
"""Scan the installed Duplicati assemblies for a literal, in BOTH encodings.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-09-22
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md section 7.3.2

Why both encodings: a .NET assembly stores user-string literals as **UTF-16LE** in the `#US`
heap, while metadata names are UTF-8. An ASCII-only `grep` over the DLLs therefore returns
false negatives for exactly the option and environment names one wants to check — round 2's
security lane hit this and reported `aes-version`, `webservice-password-init` and
`webservice-disable-signin-tokens` as absent on its first pass, before re-running in UTF-16LE.

A FOUND result is strong (the byte sequence is present); a NOT-FOUND result is weaker, because
a name composed at runtime from fragments would be invisible. Treat NOT-FOUND as "no literal",
not as "no such feature", and corroborate before acting on it.

Usage:  python3 util/ad-hoc/2026-09-22_duplicati_literal_scan.py <literal> [<literal> ...]
        python3 util/ad-hoc/2026-09-22_duplicati_literal_scan.py --root /usr/lib/duplicati ...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_ROOT = Path("/usr/lib/duplicati")


def scan(root: Path, needles: list[str]) -> int:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    blobs: list[tuple[Path, bytes]] = []
    for p in files:
        try:
            blobs.append((p, p.read_bytes()))
        except OSError:
            continue
    print(f"scanned {len(blobs)} readable files under {root}\n")

    worst = 0
    for needle in needles:
        pats = {
            "utf-8": needle.encode("utf-8"),
            "utf-16le": needle.encode("utf-16-le"),
        }
        hits: dict[str, list[str]] = {k: [] for k in pats}
        for path, blob in blobs:
            for enc, pat in pats.items():
                if pat in blob:
                    hits[enc].append(path.name)
        total = sum(len(v) for v in hits.values())
        if total == 0:
            worst = max(worst, 1)
            print(f"  NOT FOUND  {needle!r}  (0 files, utf-8 and utf-16le)")
        else:
            for enc, names in hits.items():
                if names:
                    shown = ", ".join(sorted(set(names))[:4])
                    more = "" if len(set(names)) <= 4 else f", +{len(set(names)) - 4} more"
                    print(f"  FOUND      {needle!r}  [{enc}]  {len(set(names))} file(s): {shown}{more}")
    return worst


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("literals", nargs="+")
    args = ap.parse_args()
    root = Path(args.root)
    if not root.is_dir():
        print(f"no such directory: {root}", file=sys.stderr)
        return 2
    return scan(root, args.literals)


if __name__ == "__main__":
    raise SystemExit(main())
