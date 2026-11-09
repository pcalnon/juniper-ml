#!/usr/bin/env python3
"""
Splice the rendered per-PR disposition tables into the flood-4 record's sec 5.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 disposition record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (sec 5);
         util/ad-hoc/2026-11-07_flood4_disposition_render.py (writes the tables);
         reports/2026-11-08_flood4-disposition/ (the render inputs)

WHY THIS EXISTS
Sec 5 is 74 rows rendered from the carriers' manifests and the PRs' live states. Typing them, or pasting them
by hand, is how a table drifts from what it renders. This replaces everything between the sec 5 heading and
the sec 6 heading with a fixed introduction plus the renderer's output, byte for byte, and refuses unless
each heading occurs exactly once.

Usage:
  2026-11-08_flood4_splice_sec5.py --record <notes file> --tables <renderer --out file>
"""

import argparse
import sys

SEC5 = "## §5 Per-PR disposition\n"
SEC6 = "## §6 "
INTRO = (
    "Rendered on 2026-11-08 by `util/ad-hoc/2026-11-07_flood4_disposition_render.py`. Its inputs are the six carriers' manifests and "
    "the rows no carrier holds, archived under `reports/2026-11-08_flood4-disposition/` (its README says how to re-render), and each "
    "PR's live state. A draft split across two carriers has one row naming both. \"Carried with fixes\" means the carrier changed the "
    "draft's content where triage or validation found it wrong. The evaluation column is the builder's one-line reason, cut at "
    "420 characters; the manifest holds the whole of it.\n"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", required=True)
    ap.add_argument("--tables", required=True)
    a = ap.parse_args()
    with open(a.record, encoding="utf-8") as fh:
        text = fh.read()
    with open(a.tables, encoding="utf-8") as fh:
        tables = fh.read().rstrip("\n") + "\n"
    if text.count(SEC5) != 1 or text.count("\n" + SEC6) != 1:
        raise SystemExit("REFUSING: the sec 5 heading occurs %d times, the sec 6 heading %d times" % (text.count(SEC5), text.count("\n" + SEC6)))
    start = text.index(SEC5) + len(SEC5)
    end = text.index("\n" + SEC6, start) + 1
    new = text[:start] + "\n" + INTRO + "\n" + tables + "\n" + text[end:]
    with open(a.record, "w", encoding="utf-8") as fh:
        fh.write(new)
    rows = sum(1 for line in tables.split("\n") if line.startswith("| #"))
    print("sec 5 spliced: %d table rows; record %d -> %d lines" % (rows, text.count("\n"), new.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
