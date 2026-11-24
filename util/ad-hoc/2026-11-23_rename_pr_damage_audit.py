#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml (cross-repo tooling)
# Application:   util/ad-hoc
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Created:       2026-11-23
# Status:        ad-hoc (single arc: repair of the 2026-11-20 "owner -> Overtoad" rename PRs)
"""Separate a rename PR's real rename edits from everything else it changed.

Why this exists
---------------
juniper-ml#2606 carries the owner's blind "owner -> Overtoad" substitution, then replays about 100 of
main's commits on top with scripted conflict resolution (``--ours`` / ``--theirs``), then merges main.
Its diff against the merge base mixes three things: the rename, table re-padding, and conflict damage
(main's newer text reverted, paragraphs deleted, ``Overtoadowner`` splices). A reviewer cannot tell
them apart in a 2,756-file diff. This tool inverts the substitution on the PR side and compares the
result with the base, so whatever survives the inversion is a change beyond the rename.

Classes (per modified file)
---------------------------
- ``pure-rename``    the PR file equals the base after inverting the substitution
- ``rename+format``  equal after also normalizing markdown table padding and trailing blanks
- ``BEYOND``         content differs beyond the rename (prints the residual, with ``--show``)

The inversion maps "The Overtoad" -> "Owner", "the Overtoad" -> "the owner" and "Overtoad" -> "owner",
so a case-only residual (an original "Owner" mid-sentence, say) can read as BEYOND. Read the residual
before calling a file damaged.

Usage
-----
    python3 2026-11-23_rename_pr_damage_audit.py --base BASE --head HEAD [--out classes.tsv]
        [--show PATH ...] [--context N]

Run it inside any checkout of the repository that holds both commits.
"""

from __future__ import annotations

import argparse
import collections
import difflib
import re
import subprocess
import sys

RECORD_PREFIXES = (
    "notes/releases/",
    "notes/history/",
    "notes/legacy/",
    "notes/pull_requests/",
    "prompts/thread-handoff_automated-prompts/",
    "reports/",
)
INVERSE = (
    ("The Overtoad", "Owner"),
    ("the Overtoad", "the owner"),
    ("Overtoad", "owner"),
    ("overtoad", "owner"),
    ("OVERTOAD", "OWNER"),
)
ARTIFACT_TOKENS = ("Overtoadowner", "OvertoadOvertoad", "The The Overtoad", "the The Overtoad", "<<<<<<< ", ">>>>>>> ")


def invert(text: str) -> str:
    for old, new in INVERSE:
        text = text.replace(old, new)
    return text


def normalize(line: str) -> str:
    if line.lstrip().startswith("|"):
        line = re.sub(r"-{3,}", "---", line)
        line = re.sub(r"\s*\|\s*", "|", line)
        line = re.sub(r"\s+", " ", line)
    return line.rstrip()


def raw_diff(base: str, head: str) -> list[tuple[str, str, str, str, str]]:
    """Return (old_mode, new_mode, old_sha, new_sha, path) for every MODIFIED path."""
    out = subprocess.run(["git", "diff", "--raw", "--no-renames", "--abbrev=40", base, head], check=True, capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        old_mode, new_mode, old_sha, new_sha, status = meta.lstrip(":").split()
        if status == "M":
            rows.append((old_mode, new_mode, old_sha, new_sha, path))
    return rows


def read_blobs(shas: list[str]) -> list[bytes]:
    proc = subprocess.run(["git", "cat-file", "--batch"], input=("\n".join(shas) + "\n").encode(), check=True, capture_output=True)
    data, pos, blobs = proc.stdout, 0, []
    while pos < len(data):
        newline = data.index(b"\n", pos)
        header = data[pos:newline].split()
        if len(header) < 3 or header[1] == b"missing":
            raise SystemExit(f"cat-file could not read {header!r}")
        size = int(header[2])
        blobs.append(data[newline + 1 : newline + 1 + size])
        pos = newline + 1 + size + 1
    return blobs


def classify(base_text: str, head_text: str) -> tuple[str, int, int, list[str]]:
    inverted = invert(head_text)
    if inverted == base_text:
        return "pure-rename", 0, 0, []
    base_lines = [normalize(x) for x in base_text.split("\n")]
    head_lines = [normalize(x) for x in inverted.split("\n")]
    if base_lines == head_lines:
        return "rename+format", 0, 0, []
    matcher = difflib.SequenceMatcher(None, base_lines, head_lines, autojunk=False)
    deleted = inserted = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            deleted += i2 - i1
            inserted += j2 - j1
    residual = [line for line in difflib.unified_diff(base_text.split("\n"), inverted.split("\n"), "base", "head(inverted)", n=0, lineterm="") if not line.startswith(("---", "+++"))]
    return "BEYOND", deleted, inserted, residual


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--out", help="write one TSV row per modified file")
    parser.add_argument("--show", nargs="*", default=[], help="print the residual diff for these paths")
    parser.add_argument("--context", type=int, default=12, help="residual lines to print per --show path")
    args = parser.parse_args(argv)

    rows = raw_diff(args.base, args.head)
    blobs = read_blobs([sha for row in rows for sha in (row[2], row[3])])
    counts: collections.Counter = collections.Counter()
    artifacts: collections.Counter = collections.Counter()
    table = []
    for index, (_old_mode, _new_mode, _old_sha, _new_sha, path) in enumerate(rows):
        base_text = blobs[2 * index].decode("utf-8", "surrogateescape")
        head_text = blobs[2 * index + 1].decode("utf-8", "surrogateescape")
        kind, deleted, inserted, residual = classify(base_text, head_text)
        scope = "record" if path.startswith(RECORD_PREFIXES) else "living"
        counts[(kind, scope)] += 1
        spliced = {tok: head_text.count(tok) - base_text.count(tok) for tok in ARTIFACT_TOKENS}
        spliced = {tok: n for tok, n in spliced.items() if n > 0}
        artifacts.update(spliced)
        table.append((path, scope, kind, deleted, inserted, ",".join(f"{t.strip()}x{n}" for t, n in spliced.items())))
        if path in args.show:
            print(f"##### {path}  [{kind}, -{deleted} +{inserted}]")
            for line in residual[: args.context]:
                print("  " + line[:240])
    for (kind, scope), n in sorted(counts.items()):
        print(f"{kind:14} {scope:7} {n}")
    print("splice artifacts:", dict(artifacts) or "none")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write("path\tscope\tclass\tdeleted\tinserted\tartifacts\n")
            for row in table:
                handle.write("\t".join(map(str, row)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
