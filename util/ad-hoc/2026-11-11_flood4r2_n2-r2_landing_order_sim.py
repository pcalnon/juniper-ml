#!/usr/bin/env python3
"""Simulate "the sibling carrier lands first, then this one" on the files both carriers change.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-11
Status:      ad-hoc -- one-off (round 2 of the N-2 carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
             (juniper-service-core's stop-then-start race); this carrier's stamps.json

Two uncommitted carriers (this worktree's, and a sibling's in another worktree) both edit a few
shared files: the two CHANGELOGs and the docs whose version stamps each bumps. The sibling lands
first. For each shared path this script rebuilds, in memory and under ``--scratch`` only:

1. ``main + sibling``: ``git merge-file -p <sibling's copy> <sibling's base> <main>``;
2. ``(main + sibling) + this carrier``: ``git merge-file -p <this copy> <main> <result of 1>``.

For each step it reports the number of conflicts (merge-file's exit status), where each conflict
region starts in the output, and how many lines each side holds there. For the result of step 2 it
also reports every stamp line (``**Version``, ``**Last Updated``, ``**Date``) as it then reads, so
a stamp that merges clean at the SAME value both carriers chose (and so needs the +1 by hand) is
visible. It also lists where each carrier's own hunks sit against its base.

It writes nothing outside ``--scratch`` and ``--out``; the sibling tree is read as plain files and
git is never run there. ``HEAD`` is taken as main (this worktree is reset to origin/main and holds
its carrier uncommitted).

Exit status: 0 always when the simulation ran (conflicts are a result, not an error); 2 on a
usage or setup error.

Usage (from this worktree's root):
    python3 util/ad-hoc/2026-11-11_flood4r2_n2-r2_landing_order_sim.py --sibling <sibling worktree> \\
        --sibling-base <sha> --scratch <scratch dir> --out <file.json> <path> [<path> ...]
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_STAMP = re.compile(r"^\*\*(Version|Last Updated|Date)\*?\*?:?\*?\*? ")


class SetupError(Exception):
    """The simulation could not run as designed."""


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, check=False)


def _blob(ref: str, rel: str) -> bytes:
    shown = _git("show", f"{ref}:{rel}")
    if shown.returncode != 0:
        raise SetupError(f"{ref} has no {rel}")
    return shown.stdout


def _hunks(old: bytes, new: bytes) -> list[dict]:
    """Each changed region of ``new`` against ``old``: where it starts in ``old`` and its size."""
    old_lines = old.decode("utf-8").splitlines()
    new_lines = new.decode("utf-8").splitlines()
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    return [{"op": tag, "old_line": i1 + 1, "old_lines": i2 - i1, "new_line": j1 + 1, "new_lines": j2 - j1} for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"]


def _conflicts(text: str) -> list[dict]:
    """Each conflict region in merge-file's output: its first line and the size of each side."""
    regions = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if lines[index].startswith("<<<<<<< "):
            start = index
            middle = next(i for i in range(start, len(lines)) if lines[i].startswith("======="))
            end = next(i for i in range(middle, len(lines)) if lines[i].startswith(">>>>>>> "))
            regions.append({"line": start + 1, "ours_lines": middle - start - 1, "theirs_lines": end - middle - 1, "ours_first": lines[start + 1][:100] if middle > start + 1 else "", "theirs_first": lines[middle + 1][:100] if end > middle + 1 else ""})
            index = end
        index += 1
    return regions


def _merge(work: Path, name: str, ours: bytes, base: bytes, theirs: bytes) -> tuple[int, bytes]:
    step = work / name
    step.mkdir(parents=True, exist_ok=True)
    (step / "ours").write_bytes(ours)
    (step / "base").write_bytes(base)
    (step / "theirs").write_bytes(theirs)
    merged = _git("merge-file", "-p", str(step / "ours"), str(step / "base"), str(step / "theirs"))
    if merged.returncode < 0 or merged.returncode > 127:
        raise SetupError(f"merge-file failed for {name}: {merged.stderr.decode('utf-8', 'replace')}")
    (step / "merged").write_bytes(merged.stdout)
    return merged.returncode, merged.stdout


def _stamps(data: bytes) -> list[dict]:
    return [{"line": number, "text": line} for number, line in enumerate(data.decode("utf-8").splitlines(), start=1) if _STAMP.match(line)]


def _simulate(rel: str, sibling: Path, sibling_base: str, scratch: Path) -> dict:
    main = _blob("HEAD", rel)
    sib_base = _blob(sibling_base, rel)
    sib = (sibling / rel).read_bytes()
    mine = (REPO_ROOT / rel).read_bytes()
    work = scratch / rel.replace("/", "__")
    row: dict = {"path": rel, "this_carrier_changes_it": mine != main, "sibling_changes_it": sib != sib_base, "main_changed_it_since_the_sibling_base": main != sib_base}
    row["sibling_hunks_vs_its_base"] = _hunks(sib_base, sib)
    row["this_carrier_hunks_vs_main"] = _hunks(main, mine)
    step1_exit, after_sibling = _merge(work, "1_main_plus_sibling", sib, sib_base, main)
    row["step1_main_plus_sibling"] = {"conflicts": step1_exit, "regions": _conflicts(after_sibling.decode("utf-8"))}
    step2_exit, final = _merge(work, "2_then_this_carrier", mine, main, after_sibling)
    row["step2_then_this_carrier"] = {"conflicts": step2_exit, "regions": _conflicts(final.decode("utf-8")), "stamp_lines_after": _stamps(final)}
    row["stamp_lines"] = {"main": _stamps(main), "sibling": _stamps(sib), "this_carrier": _stamps(mine)}
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sibling", required=True, type=Path, help="the sibling carrier's worktree (read as plain files)")
    parser.add_argument("--sibling-base", required=True, help="the commit the sibling carrier was built on")
    parser.add_argument("--scratch", required=True, type=Path, help="a scratch directory in this worktree's tmp/")
    parser.add_argument("--out", required=True, type=Path, help="the JSON report to write")
    parser.add_argument("paths", nargs="+", help="repository-relative paths both carriers may change")
    args = parser.parse_args(argv)

    try:
        head = _git("rev-parse", "HEAD").stdout.decode().strip()
        rows = [_simulate(rel, args.sibling, args.sibling_base, args.scratch) for rel in args.paths]
    except (SetupError, OSError) as exc:
        print(f"setup error: {exc}", file=sys.stderr)
        return 2
    result = {"main": head, "sibling": str(args.sibling), "sibling_base": args.sibling_base, "order": "sibling first, then this carrier", "files": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    for row in rows:
        step2 = row["step2_then_this_carrier"]
        print(f"{row['path']}\tsibling-first conflicts: step1 {row['step1_main_plus_sibling']['conflicts']}, step2 {step2['conflicts']}\tregions at {[r['line'] for r in step2['regions']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
