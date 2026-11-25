"""
Check (and optionally apply) code lens r23l-val-code's fixes.json against carrier r23l's files.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23l-val-code: independent validation of carrier r23l)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

For each fix, the target is the carrier's ``final/<file>`` (a repo file) or ``<carrier>/<file>`` (a ``texts/``
file). Every ``old`` must occur exactly once in its target as the carrier holds it. With ``--apply-to DIR`` the
repo-file fixes whose path starts with ``--strip-prefix`` are applied, cumulatively per file, and written to
``DIR/<path without the prefix>`` (a scratch copy; the carrier is only read).

Usage: python <this file> --fixes FILE --carrier DIR [--apply-to DIR --strip-prefix juniper-service-core/]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--fixes", required=True)
    parser.add_argument("--carrier", required=True)
    parser.add_argument("--apply-to")
    parser.add_argument("--strip-prefix", default="")
    args = parser.parse_args()
    carrier = Path(args.carrier)
    fixes = json.loads(Path(args.fixes).read_text(encoding="utf-8"))
    bad = 0
    patched: dict[str, str] = {}
    for fix in fixes:
        rel = fix["file"]
        target = carrier / rel if rel.startswith("texts/") else carrier / "final" / rel
        text = target.read_text(encoding="utf-8")
        count = text.count(fix["old"])
        status = "OK" if count == 1 else f"BAD (occurs {count} times)"
        bad += count != 1
        print(f"{fix['id']:4} {fix['severity']:6} {rel}: old {status}")
        if args.apply_to and count == 1 and not rel.startswith("texts/") and rel.startswith(args.strip_prefix):
            current = patched.get(rel, text)
            patched[rel] = current.replace(fix["old"], fix["new"])
    for rel, text in patched.items():
        out = Path(args.apply_to) / rel[len(args.strip_prefix) :]
        out.write_text(text, encoding="utf-8")
        print(f"applied -> {out}")
    print(f"{len(fixes)} fixes, {bad} with an old text that does not occur exactly once")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
