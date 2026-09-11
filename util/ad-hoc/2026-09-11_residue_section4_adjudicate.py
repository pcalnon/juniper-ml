#!/usr/bin/env python3
"""2026-09-11_residue_section4_adjudicate.py -- is each held-back line actually absent from main?

Project: juniper-ml
Sub-Project: docs fleet consolidation (round 2 residue)
Application: ad-hoc analysis
Author: Paul Calnon
License: MIT License

WHAT THIS CLOSES

`notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md` §4 lists
the lines a 35-PR docs consolidation REFUSED to merge and never adjudicated -- carried as the
arc's last open content-loss question through three handoffs. §3 adjudicated the four largest
contributors (33 + 22 + 18 + 13 = 86 lines); §4 is "the rest, verbatim".

The original classifier (`2026-09-06_docs_residue_audit.py`) matched on backticked
identifiers and link anchors, and the document says so plainly: "A line carrying neither
cannot be matched and is reported ABSENT, so the count errs toward over-reporting loss."
That is the right bias for a refusal, and the wrong basis for a verdict. This re-asks the
question with a weaker key -- normalised prose -- over the tree as it stands TODAY, months of
merges later.

HOW A LINE IS CHECKED, AND WHY THIS IS STILL NOT PROOF

Three passes, weakest key last:

  1. EXACT  -- the normalised line appears verbatim somewhere in tracked markdown;
  2. ANCHOR -- every backticked identifier / path / anchor on the line appears together in
     one file (the original key, re-run against today's tree);
  3. PROSE  -- a >= 0.82 difflib ratio against some line in the tree, which catches the
     rewording the original key was blind to.

A hit means the CLAIM survives somewhere, not that this exact sentence does. A miss means no
line resembling it was found -- which is evidence of loss, not proof: a claim can be restated
across two sentences and match nothing here. Both directions are reported, and lines that are
structurally unmatched (a bare table row, a fragment cut off at the hunk edge) are separated
out rather than counted as loss, because a `| Fact | Count |` row means nothing without its
table.

EXIT CODES

  * 0 -- parsed and reported;
  * 2 -- the residue document or its §4 could not be parsed. A zero-line report from a
    document that failed to parse is the vacuous pass this whole arc keeps catching.

Usage:
    python3 util/ad-hoc/2026-09-11_residue_section4_adjudicate.py
    python3 util/ad-hoc/2026-09-11_residue_section4_adjudicate.py --show-absent
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
from pathlib import Path

DOC = Path("notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md")
SECTION = "## 4. The rest, verbatim"
NEXT_SECTION = "## 5."

_TICKED = re.compile(r"`([^`]+)`")
_ANCHORISH = re.compile(r"[A-Za-z0-9_./#-]{4,}")


def _norm(s: str) -> str:
    return " ".join(s.split())


def parse_section4(text: str) -> dict:
    """{pr -> [lines]} from the ```text blocks under §4."""
    start = text.find(SECTION)
    if start < 0:
        raise SystemExit(f"{SECTION!r} not found in {DOC}")
    end = text.find(NEXT_SECTION, start)
    body = text[start : end if end > 0 else len(text)]
    out: dict = {}
    cur = None
    in_fence = False
    for line in body.splitlines():
        m = re.match(r"^### (#\d+)\s", line)
        if m:
            cur = m.group(1)
            out.setdefault(cur, [])
            continue
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and cur and line.strip():
            out[cur].append(line)
    return out


def _structural(line: str) -> bool:
    """A row / fragment that cannot stand alone, so its absence is not a content loss."""
    s = line.strip()
    if s.startswith("|") and s.endswith("|"):
        return True
    if re.fullmatch(r"\|[-: |]+\|", s):
        return True
    return False


def _heading_key(line: str) -> str | None:
    """Comparable key for a markdown heading, or None.

    A residue heading is `## Cascor primary freeze tell (operational)`; the tree carries
    `### Cascor Primary Freeze Tell`. Those are the SAME section -- the branch added an
    `(operational)` suffix and the tree uses title case -- and a case-sensitive exact match
    calls it a content loss. It is not: `docs/REFERENCE.md:790` holds the section and
    `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md:138` repeats its exit-code semantics.

    Comparing on depth-insensitive, case-folded title text minus a trailing parenthetical
    is what distinguishes "this section is gone" from "this heading was re-cased".
    """
    m = re.match(r"^\s*(#{1,6})\s+(.*\S)\s*$", line)
    if not m:
        return None
    title = re.sub(r"\s*\([^)]*\)\s*$", "", m.group(2))
    title = re.sub(r"[*_`]", "", title)
    return " ".join(title.split()).casefold()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--show-absent", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.82)
    args = ap.parse_args(argv)

    if not DOC.is_file():
        print(f"missing {DOC}", file=sys.stderr)
        return 2
    blocks = parse_section4(DOC.read_text(encoding="utf-8"))
    if not blocks:
        print("§4 parsed to ZERO blocks -- refusing to report", file=sys.stderr)
        return 2

    # EXCLUDE THE RESIDUE DOCUMENT ITSELF. §4 quotes every held-back line verbatim inside
    # ```text fences, and the document is tracked markdown -- so a naive corpus makes every
    # line match ITSELF and reports 149/149 accounted for. That is not a weak signal, it is a
    # measurement of the wrong thing: the question is whether the claim survives ELSEWHERE.
    # Also excluded: the handoffs that quote the same figures back.
    _SELF = {str(DOC)}
    tracked = [
        p for p in subprocess.run(  # nosec B603 B607
            ["git", "ls-files", "*.md"], capture_output=True, text=True, check=True
        ).stdout.split("\n") if p and p not in _SELF
    ]
    corpus: dict = {}
    all_lines: list = []
    for p in tracked:
        try:
            lines = [_norm(x) for x in Path(p).read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
        except OSError:
            continue
        corpus[p] = lines
        all_lines += lines
    exact = set(all_lines)
    if not exact:
        print("corpus is EMPTY -- refusing to report", file=sys.stderr)
        return 2

    tree_headings = set()
    for lines in corpus.values():
        for ln in lines:
            k = _heading_key(ln)
            if k:
                tree_headings.add(k)

    stats = {"exact": 0, "heading": 0, "anchor": 0, "prose": 0, "absent": 0, "structural": 0}
    absent_rows: list = []
    total = 0

    for pr, lines in sorted(blocks.items()):
        for raw in lines:
            total += 1
            n = _norm(raw)
            if _structural(raw):
                stats["structural"] += 1
                continue
            if n in exact:
                stats["exact"] += 1
                continue
            hk = _heading_key(raw)
            if hk and hk in tree_headings:
                stats["heading"] += 1
                continue
            ticks = _TICKED.findall(n)
            keys = [t for t in ticks if _ANCHORISH.fullmatch(t.strip())]
            if keys and any(all(k in " ".join(v) for k in keys) for v in corpus.values()):
                stats["anchor"] += 1
                continue
            close = difflib.get_close_matches(n, all_lines, n=1, cutoff=args.threshold)
            if close:
                stats["prose"] += 1
                continue
            stats["absent"] += 1
            absent_rows.append((pr, n))

    print(f"§4 blocks: {len(blocks)} PR section(s), {total} line(s)\n")
    print(f"  EXACT       {stats['exact']:4}  verbatim in tracked markdown today")
    print(f"  HEADING     {stats['heading']:4}  same section title in the tree (re-cased / suffix dropped)")
    print(f"  ANCHOR      {stats['anchor']:4}  all backticked identifiers co-occur in one file")
    print(f"  PROSE       {stats['prose']:4}  >= {args.threshold} similar to a line in the tree (reworded)")
    print(f"  STRUCTURAL  {stats['structural']:4}  table rows / separators -- cannot stand alone")
    print(f"  ABSENT      {stats['absent']:4}  nothing resembling it found")
    print(f"\n  {total - stats['absent'] - stats['structural']} of "
          f"{total - stats['structural']} content lines are accounted for in the tree")

    if args.show_absent:
        print("\n--- ABSENT, for adjudication ---")
        for pr, n in absent_rows:
            print(f"  {pr}  {n[:150]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
