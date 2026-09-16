#!/usr/bin/env python3
"""2026-09-05_markdown_structure_check.py -- catch the markdown damage a line check cannot see.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 2)
Application: ad-hoc analysis (documentation structural integrity)
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

Consolidating ten fleet docs PRs into juniper-ml#1746 dropped a single closing ``` fence
in `docs/REFERENCE.md`, and that one line swallowed **36 H2 headings** into a code block
on `main`. Three separate checks all passed on the way in:

  * the consolidator's own line-presence verifier -- blind by construction, because it
    asks "is this added line present in the result?" via a SUBSTRING test, and ``` occurs
    hundreds of times in the file. A lost fence is never "missing";
  * `juniper-docs-additions-check` -- it looks for DELETED content, and a lost fence is a
    deletion of three characters that its magnitude heuristic ignores;
  * `markdownlint` -- juniper-ml's config does not enable the link-fragment rule that
    would have flagged the now-unreachable anchors (juniper-canopy's does, which is how
    the same defect surfaced there).

The damage is invisible until someone follows a `#anchor` that no longer resolves, or a
tool like `util/soak_ledger.py verify-probes` fails on a pointer.

WHAT IT CHECKS

  * fence balance per file, naming the opening line of any unclosed fence;
  * H2 headings that sit INSIDE an UNCLOSED fence, or inside a BARE ``` fence (the actual
    symptom -- a file can have an even fence count and still swallow headings if two closes
    were lost). A CLOSED fence carrying an explicit info string (```text, ````jinja2,
    ```python) is taken at its word and is NOT checked: see `_can_swallow_headings`, which
    records the two live false positives that narrowing removed;
  * markdown tables whose header row lost its `| --- | --- |` separator, which renders the
    table as plain text and is likewise invisible to a substring check. A delimiter cell is
    valid with ONE hyphen (`| - |`, `|:-:|`), so those are tables, not findings.

Paths that resolve to the same file -- a symlink and its target, both tracked -- are
examined once and the duplicate is reported as an alias, so the count measures FILES rather
than path entries.

KNOWN LIMIT -- stated because a clean run from this screen is not proof

Fences are matched at the LINE level, so a fence nested inside a container block is
invisible to this walk: `> ```bash ` inside a blockquote, and a fence indented four or more
spaces because it sits in a list item. Cross-checked against markdown-it-py over all 1073
tracked markdown files on 2026-09-10 (`util/ad-hoc/2026-09-10_fence_walker_crosscheck.py`),
this walk disagrees with CommonMark on 215 lines in 10 files -- 184 blockquote-nested, 31
list-indented, and nothing else. The boolean toggle it replaced disagreed on 1972 lines in
89 files, and every one of the 215 is a line the toggle also got wrong: the rewrite removed
89.1% of the divergence and introduced none.

Container-relative fence tracking is deliberately NOT implemented. It needs real
container-block state, and the residual shapes produce no finding on this tree. Anyone who
widens this screen should re-run the crosscheck rather than trust the unit fixtures, which
only pin the cases their author thought of.

EXIT CODES

  * 0 -- at least one markdown file was examined and none had a structural problem;
  * 1 -- structural problems were found;
  * 2 -- the run could not report honestly: no arguments, a markdown path that could not
    be read, or ZERO paths examined. A skip that is not counted is the failure mode this
    screen exists to catch, applied to itself -- `is_file()` follows symlinks, so ten
    dangling links under `notes/` used to score clean.

Usage:
    python util/ad-hoc/2026-09-05_markdown_structure_check.py docs/*.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# GFM requires AT LEAST ONE hyphen per delimiter cell, not two: `| - |` and `|:-:|` are
# valid tables and render as tables everywhere. This pattern demanded `-{2,}` until
# 2026-09-10, so it reported every single-hyphen table as having lost its separator.
#
# That was not a counting error. `util/markdown_structure_delta.py` imports this screen and
# grades a file the PR ADDS against a baseline of zero (:165), and the step runs inside the
# `docs` job -- whose NAME, `Documentation Links`, is the REQUIRED status context. So any PR
# adding a markdown file with a valid single-hyphen delimiter row failed a required check,
# for a defect that was not in the PR. Verified against markdown-it-py: all three of
# `| - |`, `|:-:|` and `| --- |` produce a real table token.
SEPARATOR = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")


MARKDOWN_INFO_STRINGS = {"markdown", "md"}


def _is_markdown_example(opener_line: str) -> bool:
    """Does this fence declare that its CONTENT is markdown?

    ```markdown / ```md hold sample documents, so H2s inside them are the point, not a
    symptom. Anything else -- ```bash, ```python, or a bare ``` -- has no business
    containing an H2, and that is the shape a dropped closing fence produces.
    """
    return opener_line.strip().lstrip("`~").strip().lower() in MARKDOWN_INFO_STRINGS


# A fence delimiter: up to 3 spaces of indent, then >=3 backticks or >=3 tildes.
_FENCE = re.compile(r"^ {0,3}(?P<run>`{3,}|~{3,})(?P<info>.*)$")


def _info_string(opener_line: str) -> str:
    """The fence opener's info string, stripped. Empty for a BARE ``` fence."""
    m = _FENCE.match(opener_line)
    return m.group("info").strip() if m else ""


def _can_swallow_headings(opener_line: str, is_unclosed: bool) -> bool:
    """May an H2 inside THIS fence be reported as swallowed?

    Only when the fence is UNCLOSED, or carries NO info string.

    NARROWED 2026-09-15, after the previous rule -- "anything but ```markdown has no
    business containing an H2" -- was refuted by two legitimate counterexamples on `main`,
    which together were 17 of the 17 problems the whole-tree census then reported:

      * a ```text block holding an ASCII banner whose border is `#`
        (`##  HEADLESS SIGNING PREFLIGHT: BLOCKED`) -- 13 findings;
      * a ````jinja2 block holding a template that EMITS markdown, so `## Overview` is
        template OUTPUT, not document structure -- 4 findings. ml#1886 had already widened
        that fence to four backticks CORRECTLY, and this screen went on flagging it.

    This is not cosmetic. `util/markdown_structure_delta.py` grades a file the PR ADDS
    against a baseline of ZERO (:165-168), and the step runs in the `docs` job whose name,
    `Documentation Links`, is a REQUIRED status check. So an eleven-line new note with an
    ordinary ```text banner failed a required check for a defect that was not in the PR --
    the SAME failure this file's SEPARATOR comment records from the `-{2,}` regex, repeating
    in the adjacent rule.

    What is NOT lost: an unclosed fence is still reported in its own right by the UNCLOSED
    check, so no genuinely swallowed heading escapes -- it is reported under the defect that
    caused it. A BARE fence is still checked, which keeps the balanced-but-wrong (two closes
    lost) heuristic that motivated the rule: the fence that swallowed 36 headings in
    juniper-ml#1746 was bare.

    An explicit info string is the author asserting "this block is code or data of type X".
    Taking that assertion at face value is what removes the false positives.
    """
    if is_unclosed:
        return True
    if _is_markdown_example(opener_line):
        # Subsumed by the info-string test below (```markdown is never bare), but kept
        # explicit: it names the original motivating case, juniper-canopy's AGENTS.md
        # sample document, whose four permanent findings made this screen unwireable.
        return False
    return not _info_string(opener_line)


def _fence_spans(lines: list) -> tuple:
    """Walk fences the way CommonMark does, returning (in_fence_flags, openers, unclosed).

    The original walk was a BOOLEAN TOGGLE over any line starting ```, which disagrees with
    every real renderer in three ways, each of which produces a confident wrong answer
    rather than an error:

      * a CLOSING fence may not carry an info string, so ```bash never closes anything --
        it is content inside whatever block is already open;
      * a closing fence must be AT LEAST AS LONG as its opener, so ``` cannot close ````
        (four-backtick blocks exist in this repo precisely to quote three-backtick ones);
      * ``` and ~~~ are different fence characters and never close each other.

    The cost of the toggle is on the record. Two independent agents reported "three
    unclosed fences on main" in 2026-09-09's review; the reviewer confirmed it by re-running
    this screen -- the very instrument under suspicion -- and the true answer was two. The
    same toggle reports `notes/JUNIPER_2026-05-25_..._V7-IMPLEMENTATION-ROADMAP.md` as
    swallowing two H2s, when the file is a correct ````markdown sample and renders fine.

    Returns:
        in_fence: list parallel to `lines`, each entry None or the opener's (lineno, text);
        unclosed: the opener (lineno, text) left open at EOF, or None.
    """
    in_fence: list = [None] * len(lines)
    open_at = None          # (lineno, text, char, length)
    for idx, line in enumerate(lines):
        m = _FENCE.match(line)
        if m:
            run, info = m.group("run"), m.group("info")
            char, length = run[0], len(run)
            if open_at is None:
                # A backtick opener's info string may not contain a backtick (CommonMark
                # 4.5); tilde openers have no such restriction.
                if char == "`" and "`" in info:
                    pass  # not a fence opener -- fall through as ordinary content
                else:
                    open_at = (idx + 1, line, char, length)
                    in_fence[idx] = (open_at[0], open_at[1])
                    continue
            else:
                _ln, _txt, ochar, olen = open_at
                if char == ochar and length >= olen and not info.strip():
                    in_fence[idx] = (open_at[0], open_at[1])   # the closer belongs to the block
                    open_at = None
                    continue
                # Same-or-different char that cannot close: ordinary content.
        if open_at is not None:
            in_fence[idx] = (open_at[0], open_at[1])
    unclosed = (open_at[0], open_at[1]) if open_at else None
    return in_fence, unclosed


def check(path: Path) -> list:
    problems: list = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    # (1) fence balance, and (2) headings swallowed by a fence -- checked in one walk.
    #
    # A fence whose info string says it CONTAINS markdown is exempt from the heading
    # check: ```markdown blocks legitimately hold H2s, because they are showing the
    # reader what a document should look like. juniper-canopy's AGENTS.md carries one
    # (a sample `notes/history/INDEX.md`) with four such headings, and flagging it made
    # this checker unwireable as a gate -- four permanent false findings on a clean
    # tree. Every other info string, and a BARE fence, is still checked: the fence that
    # swallowed 36 headings in juniper-ml#1746 was not a markdown example.
    spans, unclosed = _fence_spans(lines)
    for i, line in enumerate(lines, 1):
        opener = spans[i - 1]
        if opener is None or _FENCE.match(line):
            continue
        is_unclosed = unclosed is not None and opener[0] == unclosed[0]
        if line.startswith("## ") and _can_swallow_headings(opener[1], is_unclosed):
            problems.append(
                f"H2 swallowed by the fence opened at line {opener[0]} "
                f"({opener[1].strip()[:20]!r}): line {i}: {line.strip()[:60]}"
            )
    if unclosed:
        problems.append(f"UNCLOSED code fence opened at line {unclosed[0]}: {unclosed[1][:60]!r}")

    # (3) table header with no separator row.
    for i, line in enumerate(lines):
        if spans[i] is not None:
            continue
        # A four-space indent is an INDENTED CODE BLOCK -- CommonMark reads it as literally as a
        # fence, so a quoted `| ... |` row inside one is not a table. Found by writing this
        # tool's own findings to a notes document, where the quoted rows are indented precisely
        # because a fence would be closed by a residue line that contains one.
        if line[:4] == "    ":
            continue
        stripped = line.strip()
        if stripped.startswith("|") and line.count("|") >= 2:
            prev = lines[i - 1] if i else ""
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if not prev.strip().startswith("|") and nxt.strip().startswith("|") and not SEPARATOR.match(nxt):
                problems.append(f"table at line {i+1} has no separator row: {stripped[:60]}")
    return problems


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    total = 0
    examined = 0
    unreadable: list = []
    not_markdown: list = []
    aliases: list = []
    seen: dict = {}
    for arg in argv:
        p = Path(arg)
        if p.suffix.lower() != ".md":
            # A legitimate filter -- callers hand in mixed globs -- but it is COUNTED, so a
            # run that filtered away everything cannot report success. See the examined == 0
            # guard below.
            not_markdown.append(arg)
            continue
        # A symlink and its target are TWO tracked paths and ONE file. Repointing the ten
        # broken notes links (2026-09-10) made `notes/development/...V7-IMPLEMENTATION-
        # ROADMAP.md` resolve onto `notes/JUNIPER_2026-05-25_...`, which already had two
        # findings -- so the whole-tree count rose 63 -> 65 while not one character of
        # markdown had changed. Deduplicating by resolved path reports the file once.
        #
        # This is a dedup, NOT a skip: the alias is counted and named below. A silent skip
        # is the exact failure this screen was built to catch, and adding one here to tidy
        # a number would reintroduce it one level up.
        try:
            real = p.resolve(strict=True)
        except OSError as exc:
            unreadable.append(f"{arg}: {exc}")
            continue
        if real in seen:
            aliases.append(f"{arg} -> same file as {seen[real]}")
            continue
        seen[real] = arg
        try:
            found = check(p)
        except OSError as exc:
            # NOT a silent skip. The old predicate was `not p.is_file()`, and `is_file()`
            # FOLLOWS SYMLINKS -- a dangling link answers False, so it was skipped without
            # being counted and the run scored it clean. `main` carries ten such links (nine
            # in notes/legacy/ pointing at a `regressions/` directory that is not on main,
            # one under notes/development/), so the headline count was over 1024 of 1034
            # paths while reporting as though it covered all of them.
            unreadable.append(f"{arg}: {exc}")
            continue
        examined += 1
        if found:
            total += len(found)
            print(f"=== {arg} ===")
            for f in found:
                print(f"   {f}")
    print(f"\nstructural problems: {total}")
    print(
        f"examined {examined} of {len(argv)} path(s)"
        + (f"; skipped {len(not_markdown)} non-markdown" if not_markdown else "")
        + (f"; {len(aliases)} symlink alias(es) of an already-examined file" if aliases else "")
    )
    for item in aliases:
        print(f"    alias: {item}")

    if unreadable:
        print(f"could not read {len(unreadable)} markdown path(s):", file=sys.stderr)
        for item in unreadable:
            print(f"    {item}", file=sys.stderr)
        print("refusing to report on a partial examination", file=sys.stderr)
        return 2
    if examined == 0:
        # Every path was filtered or unreadable. A correct predicate over an empty site set
        # reports "no problems" -- the vacuous pass this guard exists to refuse.
        print(f"examined 0 of {len(argv)} path(s) -- refusing to report success", file=sys.stderr)
        return 2
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
