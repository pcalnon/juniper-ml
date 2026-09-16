#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   CI gate
# File Name:     markdown_structure_delta.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#   Fail a PR that BREAKS markdown structure, without demanding a clean tree first.
#
#   `util/ad-hoc/2026-09-05_markdown_structure_check.py` counts three defects a lost fence or a
#   whole-line union produces: unbalanced fences, H2 headings swallowed by one, and a table whose
#   header has no separator row. Markdownlint and the doc-link validator see none of them -- a
#   fence is never "missing", it silently absorbs everything after it.
#
#   Wiring that count directly as a gate does not work, and the measurement says so -- even
#   now that the count is **zero across 1084 paths** (2026-09-15). It reached zero in two
#   steps: the 2026-09-10 repair cleared the real damage, and the 2026-09-15 rule narrowing
#   cleared the last 17, which were screen FALSE POSITIVES no repair could clear without lying
#   about the content (a ```text block of banner art whose lines begin `## `, and a ````jinja2
#   template sample whose H2s are the sample).
#
#   ZERO IS NOT A REASON TO DROP THE DELTA SCOPING. The count regresses the moment damage
#   lands, and a gate demanding zero is red on arrival from that commit until someone repairs
#   a file they may not have touched. The per-file/per-PR comparison is also correct on its
#   own terms: an untouched file is not the PR's problem.
#
#   THE COUNT IS A MOVING FLOOR, NOT A BACKLOG, and treating it as a standing fact is how five
#   sites in this repo went stale at once. Successive measurements: 104/23 (09-05), 102/21
#   (09-09), 63/14 after ml#1834 repaired the live `notes/` half, 73/15 later the same day,
#   63/14 (09-10 morning), 17/2 (09-10 structure repair), 0/0 (09-15 rule narrowing).
#   Quote a commit and a date, or re-measure --
#   never the bare number. ml#1881 demonstrated the other failure mode: a branch cut before
#   ml#1880 re-introduced the stale 102/21 into two of the six sites ml#1880 had just fixed,
#   nine hours after it merged. A figure duplicated across files does not stay corrected.
#
#   This comment also said the damage was "most of them in `notes/legacy/` and
#   `notes/code-review/`", and that is FALSE. It concentrated in live `notes/` and `prompts/`.
#
#   the 2026-09-10 structure repair then repaired the real damage rather than delta-scoping around it -- a ```python
#   fence that had swallowed 161 lines of `notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md`
#   after two documents were welded onto one line, two genuinely unclosed fences under
#   `prompts/`, two broken tables, and a jinja2 wrapper that let `{% endblock %}` render as
#   prose on github.com -- so the remaining 17 are a floor made entirely of false positives.
#
#   RE-MEASURE BEFORE QUOTING, and delimit the paths properly:
#
#       git ls-files -z '*.md' | xargs -0 python3 \
#           util/ad-hoc/2026-09-05_markdown_structure_check.py
#
#   Bare `xargs` splits on WHITESPACE, so a tracked path containing a space becomes two
#   arguments: the run then reports 1040 paths against 1034 tracked and invents six
#   "non-markdown" fragments. The totals survive that, the coverage line does not.
#
#   The run exited 2, not 0/1, for as long as `main` carried ten DANGLING symlinks under
#   `notes/` that the screen counts as unreadable and refuses to certify around (#1831), so
#   every count before the 2026-09-10 structure repair was a floor over the READABLE set rather than a whole-tree
#   census. The 2026-09-10 structure repair retargeted all ten -- `432ed644` had renamed both ends and a symlink body
#   is opaque text, so nothing rewrote it -- and the screen now examines every tracked path
#   and exits 1. It also reports SYMLINK ALIASES: eleven tracked paths resolve onto a file
#   another path already covered (CLAUDE.md -> AGENTS.md among them), and counting those twice
#   had inflated the total by 2 the moment the links began resolving.
#
#   So gate the DELTA, per FILE, over only the files the PR TOUCHES:
#
#     * a file the PR does not touch cannot be broken by the PR, however broken it already is;
#     * a file the PR touches must not come out with MORE problems than it went in with;
#     * a file the PR ADDS starts from zero, so it must be clean.
#
#   Inherited damage is therefore invisible and newly-inflicted damage is not, which is the only
#   split that lets the gate go in today.
#
#   FAIL-CLOSED ON AN EMPTY *OR PARTIAL* EXAMINATION. The screen silently skips anything that is
#   not a `.md` file, so a bad glob or a wrong base ref examines nothing and reports success -- a
#   correct predicate over an empty site enumeration. Three refusals cover it:
#
#     * `base == head` is not a comparison (ci.yml's non-PR fallback yields it on a root commit);
#     * ANY touched file unreadable at head -- not just all of them, because nine read and one
#       skipped is the same failure one file at a time;
#     * zero files examined while the diff named markdown.
#
# Usage:
#   markdown_structure_delta.py --base <ref> [--head <ref>]
#
# Exit: 0 clean or no markdown touched; 1 when a touched file gained problems; 2 on an
#       invocation error (unresolvable ref, or an examination that saw nothing).
#####################################################################################################################################################################################################
"""Fail a PR that increases markdown structure problems in a file it touches."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess  # nosec B404 -- fixed argv git invocations, no shell
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREEN = REPO_ROOT / "util" / "ad-hoc" / "2026-09-05_markdown_structure_check.py"


def _load_screen():
    spec = importlib.util.spec_from_file_location("markdown_structure_check", SCREEN)
    if spec is None or spec.loader is None:  # pragma: no cover -- packaging accident
        raise SystemExit(f"cannot load {SCREEN}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True, timeout=300, check=False)


def touched_markdown(base: str, head: str) -> list[str]:
    """Markdown paths the PR changed, deletions excluded -- a deleted file has no head state."""
    res = git("diff", "--name-only", "--diff-filter=d", f"{base}...{head}", "--", "*.md")
    return [p for p in res.stdout.splitlines() if p.strip()]


def problems_at(screen, ref: str, rel: str) -> int | None:
    """Problem count for `rel` as `ref` had it, or None when `ref` does not have the file."""
    blob = git("show", f"{ref}:{rel}")
    if blob.returncode != 0:
        return None
    with tempfile.TemporaryDirectory() as td:
        # Materialise under the ORIGINAL basename: the screen skips anything not ending `.md`,
        # so a sanitised temp name would silently examine nothing and pass.
        path = Path(td) / Path(rel).name
        path.write_text(blob.stdout, encoding="utf-8")
        return len(screen.check(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="merge-base side of the comparison")
    parser.add_argument("--head", default="HEAD", help="PR head (default HEAD)")
    args = parser.parse_args(argv)

    for ref in (args.base, args.head):
        if git("rev-parse", "--verify", "-q", f"{ref}^{{commit}}").returncode != 0:
            print(f"cannot resolve ref {ref!r}", file=sys.stderr)
            return 2

    if git("rev-parse", args.base).stdout.strip() == git("rev-parse", args.head).stdout.strip():
        # base == head is not a comparison. ci.yml's fallback for a non-`pull_request` event is
        # `git rev-parse HEAD^1 || git rev-parse HEAD`, and on a root commit that second arm
        # yields HEAD itself -- an empty diff, "no markdown touched", exit 0. Vacuous.
        print(f"base and head are the same commit ({args.base}) -- that is not a comparison", file=sys.stderr)
        return 2

    touched = touched_markdown(args.base, args.head)
    if not touched:
        print("no markdown touched by this PR -- nothing to compare")
        return 0

    screen = _load_screen()
    examined = 0
    unreadable: list[str] = []
    regressions: list[str] = []
    for rel in touched:
        after = problems_at(screen, args.head, rel)
        if after is None:
            # NOT a silent continue. Skipping without counting means nine readable files and one
            # unreadable reports success and says nothing about the tenth -- the same
            # examined-nothing failure this guard exists for, one file at a time.
            unreadable.append(rel)
            continue
        examined += 1
        before = problems_at(screen, args.base, rel)
        if before is None:
            before = 0  # a file the PR ADDS starts from zero, so it must be clean
            label = "added"
        else:
            label = "changed"
        if after > before:
            regressions.append(f"{rel} ({label}): {before} -> {after}")
        print(f"  {'FAIL' if after > before else 'ok  '} {rel}: {before} -> {after}")

    if unreadable:
        print(f"could not read {len(unreadable)} of {len(touched)} touched markdown file(s) at {args.head}:", file=sys.stderr)
        for rel in unreadable:
            print(f"    {rel}", file=sys.stderr)
        print("refusing to report on a partial examination", file=sys.stderr)
        return 2

    if examined == 0:
        # The diff named markdown and none of it was examined. The screen skips non-`.md` files
        # silently, so this is the shape where a correct predicate runs over an empty site set
        # and reports success.
        print(f"examined 0 of {len(touched)} touched markdown file(s) -- refusing to report success", file=sys.stderr)
        return 2

    print()
    print(f"examined {examined} touched markdown file(s); {len(regressions)} regression(s)")
    if regressions:
        print()
        print("FAIL: these files gained structural problems:")
        for line in regressions:
            print(f"    {line}")
        print()
        print("An unbalanced fence swallows every heading after it, and a table row with no")
        print("separator renders as paragraph text. Neither is visible to markdownlint or to")
        print("the doc-link validator.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
