#!/usr/bin/env python3
"""
Stage a carrier's validated PR texts for the signed push: title.txt, pr_body.md with the attribution footer, and
commit_body.txt whose LAST paragraph is the trailer block.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12 (session-8 copy 2026-11-14: Co-Authored-By names the model this session runs on, Opus 5.5)
Status: ad-hoc — one-off (Cursor flood-4 session 6: landing the validated carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_land_open_pr.py (reads the directory this writes),
         util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py (reads title.txt and commit_body.txt)

Why: a builder delivers pr_title.txt, pr_body.txt (sometimes with a first line ``TITLE: ...``) and commit_body.txt
with no footer and no trailers. The orchestrator then corrects what a ruling or a merge made stale, adds the footer
and the trailers, and must keep any ``Allow-Symbol-Loss:`` / ``Allow-Docs-Rewrite:`` waiver in the commit body's final
paragraph, where the sequence-safety screens and git's trailer parser both read it. Done by hand, that step dropped a
line break once and shipped one pull request (juniper-ml#2552) without the waiver it needed.

Usage:
  2026-11-12_flood4r2_s6_stage_texts.py --title-file <f> --body-file <f> --commit-body-file <f> --out <texts dir>
      --session-url <https://claude.ai/code/session_...>
      [--replace-body OLD NEW ...] [--replace-commit OLD NEW ...] [--trailer "Key: value" ...]
      [--commit-paragraph <file>]

Every OLD must occur exactly once in its text, or nothing is written. ``\\n`` inside OLD or NEW is a line break.
``--commit-paragraph`` is appended to the commit body as its own paragraph, above the trailer block (the rationale
of a waiver). ``--trailer`` lines are put first in the trailer block, then Co-Authored-By and Claude-Session.
A first body line ``TITLE: <title>`` is checked against the title file and removed. Refuses a CI-skip marker in any
of the three texts and a title that is not one line.
Writes <out>/title.txt, <out>/pr_body.md and <out>/commit_body.txt, and prints each text's last lines. Exit 0 =
written; 1 = refused.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

FOOTER = "\U0001f916 Generated with [Claude Code](https://claude.com/claude-code)"
CO_AUTHOR = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
SKIP_MARKERS = ("[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]", "skip-checks:")


def apply(text: str, pairs: list[list[str]], what: str) -> str:
    for old, new in pairs:
        old = old.replace("\\n", "\n")
        new = new.replace("\\n", "\n")
        count = text.count(old)
        if count != 1:
            raise SystemExit("REFUSED: %s: the old text occurs %d time(s), not once: %r" % (what, count, old[:90]))
        text = text.replace(old, new)
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title-file", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--commit-body-file", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--session-url", required=True)
    parser.add_argument("--replace-body", nargs=2, action="append", default=[], metavar=("OLD", "NEW"))
    parser.add_argument("--replace-commit", nargs=2, action="append", default=[], metavar=("OLD", "NEW"))
    parser.add_argument("--trailer", action="append", default=[])
    parser.add_argument("--commit-paragraph")
    args = parser.parse_args()

    title = Path(args.title_file).read_text(encoding="utf-8").strip()
    if title.startswith("TITLE: "):
        title = title[len("TITLE: ") :].strip()
    if "\n" in title or not title:
        print("REFUSED: the title must be exactly one line")
        return 1

    body = Path(args.body_file).read_text(encoding="utf-8")
    first, _, rest = body.partition("\n")
    if first.startswith("TITLE: "):
        if first[len("TITLE: ") :].strip() != title:
            print("REFUSED: the body's TITLE line differs from the title file")
            return 1
        body = rest.lstrip("\n")
    body = apply(body, args.replace_body, "pr body")
    body = body.rstrip("\n") + "\n\n" + FOOTER + "\n\n" + args.session_url + "\n"

    commit = Path(args.commit_body_file).read_text(encoding="utf-8")
    commit = apply(commit, args.replace_commit, "commit body").rstrip("\n")
    if args.commit_paragraph:
        commit += "\n\n" + Path(args.commit_paragraph).read_text(encoding="utf-8").strip("\n")
    for trailer in args.trailer:
        key, sep, value = trailer.partition(": ")
        if not sep or not key or " " in key or not value.strip() or "\n" in trailer:
            print("REFUSED: not a one-line 'Key: value' trailer: %r" % trailer[:80])
            return 1
    block = list(args.trailer) + [CO_AUTHOR, "Claude-Session: " + args.session_url]
    commit += "\n\n" + "\n".join(block) + "\n"

    joined = (title + "\n" + body + "\n" + commit).lower()
    for marker in SKIP_MARKERS:
        if marker in joined:
            print("REFUSED: a CI-skip marker (%s) is in the texts" % marker)
            return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "title.txt").write_text(title + "\n", encoding="utf-8")
    (out / "pr_body.md").write_text(body, encoding="utf-8")
    (out / "commit_body.txt").write_text(commit, encoding="utf-8")
    print("title (%d chars): %s" % (len(title), title[:170]))
    print("pr_body.md: %d chars; last lines:" % len(body))
    for line in body.rstrip("\n").split("\n")[-4:]:
        print("   | " + line[:150])
    last = commit.rstrip("\n").split("\n\n")[-1].split("\n")
    print("commit_body.txt: %d chars; final paragraph keys: %s" % (len(commit), [line.split(":")[0] for line in last]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
