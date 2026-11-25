#!/usr/bin/env python3
"""Apply a validator's proposed old->new edits to COPIES of a port's frozen files, for re-proving (V26 CODE lens).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (validation of the ruling-26 lockfile-print ports; tmp/flood4/session11/r26/val_code/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session11/briefs/V26_ports_validator.txt (CODE lens; "do not fix the deliverables yourself")

Reads --fixes (a JSON list of {repo, path, old, new}), and for --repo copies --final/<path> for every path in --paths
into --out/final/<path>, applies that repo's edits to the copies (each OLD must occur exactly once in its file, or the
script stops), and writes --out/paths.txt and --out/final.sha256 in the frozen set's own format. The frozen
deliverables are only read, never written.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_code_propose.py --fixes JSON --repo NAME --final DIR --paths FILE --out DIR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fixes", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--final", type=Path, required=True)
    parser.add_argument("--paths", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with args.fixes.open(encoding="utf-8") as fh:
        fixes = [fix for fix in json.load(fh) if fix["repo"] == args.repo]
    rel_paths = [line.strip() for line in args.paths.read_text(encoding="utf-8").splitlines() if line.strip()]
    sums = []
    for rel in rel_paths:
        target = args.out / "final" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.final / rel, target)
        text = target.read_text(encoding="utf-8")
        for fix in (f for f in fixes if f["path"] == rel):
            count = text.count(fix["old"])
            if count != 1:
                print(f"STOP: {args.repo} {rel}: OLD occurs {count} times: {fix['old'][:80]!r}", file=sys.stderr)
                return 2
            text = text.replace(fix["old"], fix["new"], 1)
            print(f"applied to {rel}: {fix['old'].strip()[:70]!r} -> {fix['new'].strip()[:70]!r}")
        target.write_text(text, encoding="utf-8")
        sums.append(f"{hashlib.sha256(target.read_bytes()).hexdigest()}  {rel}")
    (args.out / "paths.txt").write_text("\n".join(rel_paths) + "\n", encoding="utf-8")
    (args.out / "final.sha256").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
