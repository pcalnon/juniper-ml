#!/usr/bin/env python3
"""Markdown STRUCTURE damage a line-level diff check cannot see.

*** PREFER util/markdown_structure_delta.py -- IT IS THE ONE WIRED INTO CI. ***

Two things to know before running this.

**It is not the file its name suggests.** `util/ad-hoc/2026-09-05_markdown_structure_check.py`
is a DIFFERENT script, one word apart in the filename. That one is the screen
`util/markdown_structure_delta.py` imports, and it is what the `Markdown structure (delta
against the merge-base)` CI step actually executes. This file is a standalone verifier and is
wired into nothing.

**FOUR blind spots were FIXED 2026-09-15 (owner-ruled). They had been documented and left
for ten days, which is its own lesson: a documented defect is still a defect.**

  * the VCS command was absent from the `CODEY` alternation, so every such command line was
    invisible to the unfenced-command count. Measured on `docs/REFERENCE.md` 2026-09-08: 14
    lines against 186 the list did cover -- a real hole and a MODEST one, roughly 7%, not the
    ~38% an earlier handoff quoted. Now covered, along with docker/conda/pytest/uv/npx;
  * check C2 was set-membership, so N copies of a line the base carried once all passed.
    Now counts MULTIPLICITY (`_newly_added`);
  * check C3 had the identical set-membership defect one line below C2 and was NOT in the
    documented list at all -- found only by reading the neighbour while fixing C2. Fixed the
    same way;
  * check C4 was a NET count, so a heading lost and another gained cancelled to "no change".
    Now compares heading TEXTS as a multiset and names what was lost;
  * a missing path, a new file, or an unresolvable `--base` all printed OK and exited 0 -- a
    correct predicate over an empty site enumeration, the failure this whole family of tools
    keeps re-introducing. Now: an unresolvable base exits 2 before any path is read, an
    unreadable path exits 2 rather than letting its siblings certify around it, examining
    zero paths exits 2, and a NEW file is checked ABSOLUTELY against an empty base (C1/C3
    still apply) instead of being skipped.

**Still blind, by design:** DUPLICATION. A re-landed section balances its own fences, keeps
its separators and RAISES the heading count, so every check here passes -- that is exactly
how juniper-ml#1799's 367 duplicated lines reached `main` with a clean report. Use
`util/ad-hoc/2026-09-07_duplicate_section_census.py` for that; it is not this tool's job.

Retained because its fence-parity reasoning below is still the clearest statement of why
balance alone is insufficient. Do not use it as a gate.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc verification tooling (docs consolidation)
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-05
Status:      ad-hoc -- verification, SUPERSEDED as a gate by util/markdown_structure_delta.py
Retire when: the consolidator runs this itself, or docs stop being merged N-way.
Related:     util/ad-hoc/2026-09-05_fleet_docs_consolidate.py (--verify checks
             LINES; this checks STRUCTURE),
             util/ad-hoc/2026-09-05_verify_consolidation_carried.py.

WHY -- THREE REAL DEFECTS, NONE OF THEM A MISSING LINE

Consolidating flood-2 docs PRs on 2026-09-05 produced, across two batches:

  1. a ```bash PAIR removed (batch 1, #1628; twice) -- 17 lines of shell left as
     bare prose;
  2. an UNCLOSED ```text fence (batch 2, #1639) -- flips fence parity for the
     REST OF THE FILE, so the unfenced-command count went 6 -> 78;
  3. a `### Operator pitfalls` heading AND its table header removed, orphaning
     seven table rows -- a table with no header does not render as a table.

The consolidator's own `--verify` passed all three: every one is present as
LINES and absent only as STRUCTURE. Nor does markdownlint catch (1) or (3).

WHY FENCE BALANCE IS NOT ENOUGH -- both halves of the lesson

  removing a matched PAIR   -> count stays EVEN, balance check passes  (batch 1)
  removing ONE fence        -> count goes ODD, but says nothing about where (batch 2)

So parity is necessary and not sufficient. The load-bearing check is C2:
command-looking lines OUTSIDE any fence, COMPARED TO THE BASE. The comparison is
base-relative because a file may legitimately carry such a line in prose, and an
absolute threshold would then fail always or never.

RATIFICATION WITHDRAWN 2026-09-16. This paragraph used to justify the base-relative
form by pointing at "6 in a pre-existing `memory_index_check` block" in
`docs/REFERENCE.md`. Those six were NOT pre-existing: they were juniper-ml#1746's
residue -- an unfenced `### Usage` block whose six commands rendered as prose -- and
the flood-2 handoff said explicitly to fence them rather than ratify them. They were
fenced on 2026-09-16, and `docs/REFERENCE.md` now measures ZERO unfenced command
lines, so C2's base for it is 0 and the check is strictly sharper there. Calling
damage "pre-existing" is how a base-relative check quietly grandfathers the thing it
was built to find.

CHECKS

  C1  fence parity is even
  C2  no NEW command-looking line outside a fence, vs the base
  C3  no NEW table row whose table has no header row above it
  C4  heading count did not DROP (the swallowed-heading signature of #1749)

Usage
-----
    python3 util/ad-hoc/2026-09-05_md_structure_check.py --base origin/main \
        docs/REFERENCE.md docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
from collections import Counter

FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
# An ALLOWLIST, and so permanently incomplete -- it can only miss commands nobody has
# thought of yet. The VCS command was absent until 2026-09-15, measured at 14 invisible
# lines in docs/REFERENCE.md against 186 the list covered (~7%, not the ~38% an earlier
# handoff quoted). The names added with it are tools that do not plausibly begin an
# English sentence; that is the bar for adding one, because `make` is already here and
# "make sure ..." is ordinary prose.
#
# RE-MEASURE rather than assume: widen the alternation to `\S+` in a scratch copy and diff
# the lines it then reports against this list to see what is still invisible.
CODEY = re.compile(
    r"^(python3?|bash|gh|pip|cd|export|make|sudo|npm|curl|"
    r"git|docker|conda|pytest|uv|npx|"
    r"LD_LIBRARY_PATH=|LIBTORCH=|JUNIPER_|CASCOR_)\b"
)
ROW = re.compile(r"^\s*\|.*\|\s*$")
SEP = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
HEADING = re.compile(r"^#{1,6}\s")


def base_text(base: str, path: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{base}:{path}"],
                          capture_output=True, text=True, check=False)
    return proc.stdout if proc.returncode == 0 else None


def analyse(text: str) -> dict:
    """Structure of the OUT-OF-FENCE prose.

    The table rule needs LOOKAHEAD, not lookbehind. A header row is legitimately
    the first row of its block, so "first row of a block" is not the defect --
    an earlier version of this check used exactly that and flagged every
    well-formed table in the file. What makes a table orphaned is that its block
    has no `|---|---|` SEPARATOR as its second line. So: group contiguous rows
    into blocks and judge the block.
    """
    lines = text.splitlines()
    inside = False
    unfenced, headless_rows, headings, fences = [], [], 0, 0
    heading_texts: list = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if FENCE.match(ln):
            fences += 1
            inside = not inside
            i += 1
            continue
        if inside:
            i += 1
            continue
        if HEADING.match(ln):
            headings += 1
            heading_texts.append(" ".join(ln.split()))
        if CODEY.match(ln):
            unfenced.append(" ".join(ln.split()))
        if ROW.match(ln):
            block_start = i
            while i < len(lines) and ROW.match(lines[i]):
                i += 1
            block = lines[block_start:i]
            has_sep = len(block) >= 2 and SEP.match(block[1])
            if not has_sep:
                headless_rows.append(" ".join(block[0].split()))
            continue
        i += 1
    return {
        "fences": fences,
        "unfenced": unfenced,
        "headless_rows": headless_rows,
        "headings": headings,
        # The TEXTS, not just the count. C4 compares multisets so that a heading lost and
        # an unrelated heading gained in the same PR no longer cancel to "no change".
        "heading_texts": heading_texts,
    }


def base_ref_exists(base: str) -> bool:
    """Does the base ref resolve to a commit at all?

    An unresolvable `--base` used to make every comparison vacuous WITHOUT saying so:
    `base_text` returned None for each path, every path took the `[NEW ]` branch, and the
    run printed OK and exited 0. A typo'd ref therefore certified a tree nobody examined.
    """
    proc = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"],
                          capture_output=True, text=True, check=False)
    return proc.returncode == 0


def _newly_added(head: list, base: list) -> list:
    """Items in `head` beyond what `base` already carried, COUNTING MULTIPLICITY.

    Replaces `[x for x in head if x not in base]`, which was set membership: if the base
    carried a line once, ANY number of copies in the head passed. A duplicated block is
    precisely what a bad consolidation produces (juniper-ml#1799 landed 367 duplicated
    lines), so the check was blind to its own motivating damage.

    Called both ways round: (head, base) gives what the PR ADDED; (base, head) gives what
    it LOST, which is how C4 stops a loss and an unrelated gain from cancelling.
    """
    remaining = Counter(base)
    out = []
    for item in head:
        if remaining[item] > 0:
            remaining[item] -= 1
        else:
            out.append(item)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()

    if not base_ref_exists(args.base):
        print(f"[ERR ] base ref {args.base!r} does not resolve to a commit.")
        print("       Refusing to report: every comparison against it would be vacuous.")
        return 2

    rc = 0
    examined = 0
    unreadable: list = []
    for path in args.paths:
        bt = base_text(args.base, path)
        try:
            with open(path) as f:
                ht = f.read()
        except OSError as exc:
            # NOT a silent skip. A path that cannot be read is the examined-nothing failure
            # this screen exists to catch, applied to itself -- it used to print [SKIP] and
            # leave the exit code untouched, so nine readable files certified the tenth.
            unreadable.append(f"{path}: {exc}")
            print(f"[ERR ] {path}: {exc}")
            continue
        if bt is None:
            # A file the PR ADDS has no base. That is not a reason to skip it: C1 (fence
            # parity) and C3 (headless tables) are ABSOLUTE checks and still apply. Compare
            # against an empty base so they run, rather than reporting OK on an unexamined
            # file -- which is how a new file with a broken table used to pass.
            print(f"[NEW ] {path}: not on {args.base}; C1/C3 checked absolutely")
            bt = ""

        examined += 1
        b, h = analyse(bt), analyse(ht)
        fails = []

        if h["fences"] % 2:
            fails.append(f"C1 fence parity ODD ({h['fences']}) — an unclosed fence "
                         f"unfences the rest of the file")

        new_unfenced = _newly_added(h["unfenced"], b["unfenced"])
        if new_unfenced:
            fails.append(f"C2 {len(new_unfenced)} NEW command line(s) outside a fence "
                         f"(base has {len(b['unfenced'])})")
            for x in new_unfenced[:5]:
                fails.append(f"      {x[:110]}")

        # Same multiplicity fix as C2. Fixing one and leaving its neighbour would have left
        # the identical defect one line away.
        new_headless = _newly_added(h["headless_rows"], b["headless_rows"])
        if new_headless:
            fails.append(f"C3 {len(new_headless)} NEW table row(s) with no header above")
            for x in new_headless[:5]:
                fails.append(f"      {x[:110]}")

        # NOT a net count. `h < b` reported nothing when a PR dropped two headings and added
        # two others -- which is what a swallowed section plus new prose looks like.
        lost_headings = _newly_added(b["heading_texts"], h["heading_texts"])
        if lost_headings:
            fails.append(f"C4 {len(lost_headings)} heading(s) LOST "
                         f"(count {b['headings']} -> {h['headings']}; the #1749 "
                         f"swallowed-heading signature, which a net count could hide)")
            for x in lost_headings[:5]:
                fails.append(f"      {x[:110]}")

        if fails:
            rc = 1
            print(f"[FAIL] {path}")
            for f in fails:
                print(f"   {f}")
        else:
            print(f"[ OK ] {path}  fences={h['fences']} headings={h['headings']} "
                  f"unfenced={len(h['unfenced'])} (base {len(b['unfenced'])})")

    print()
    if unreadable:
        print(f"ERROR: {len(unreadable)} path(s) could not be read; refusing to certify "
              f"the rest around them:")
        for u in unreadable:
            print(f"   {u}")
        return 2
    if examined == 0:
        print("ERROR: examined ZERO paths. A correct predicate over an empty site "
              "enumeration is the failure this screen exists to catch.")
        return 2
    print("FAIL: markdown structure regressed." if rc else
          f"OK: no structural regression against the base ({examined} path(s) examined).")
    return rc


if __name__ == "__main__":
    sys.exit(main())
