#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice)
# Author:        Paul Calnon
# Version:       0.2.0
# License:       MIT License
#
# Single-use. Assemble several group patches that were each built against the SAME base commit
# into one tree, file by file, WITHOUT a line-level merge.
#
# v0.1.0 used `git merge-file --union`, and that interleaved two runbooks inserted at one anchor:
# both insertions contained the same boilerplate lines (a closing ``` fence, blanks, `### Pitfalls`),
# and diff3 aligned those lines ACROSS the two blocks, so one section's code fence closed inside the
# next section. An insertion must be treated as an opaque block.
#
# v0.2.0 reads each unified diff's hunks and turns them into exact edit operations on the BASE:
#     (base_start, base_end, new_lines)   -- base[base_start:base_end] is replaced by new_lines
# A pure insertion has base_start == base_end. All groups' operations on one file are merged:
#   * insertions at the same base position are concatenated as whole blocks, in patch order;
#   * two operations that replace overlapping base ranges are a CONFLICT -- reported, and the file
#     is NOT written (the caller resolves it by hand);
#   * an insertion at p and a replacement starting at p keep the insertion first.
#
# Writes into --out (a scratch directory mirroring repo paths). With --apply it also copies the
# results into --repo's working tree. It never commits, stages, or touches git state.
#
# Usage:
#   2026-10-08_flood3_canopy_docs_assemble.py --repo <wt> --base <sha> --out <dir> [--apply] p1.patch p2.patch ...
"""Assemble per-group patches built against one base, keeping insertions as opaque blocks."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_patch(text: str) -> dict[str, list[tuple[int, int, list[str]]]]:
    """Return {path: [(base_start0, base_end0, new_lines), ...]} with 0-based base indices."""
    ops: dict[str, list[tuple[int, int, list[str]]]] = {}
    path = None
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("+++ "):
            path = line[6:].rstrip("\n") if line.startswith("+++ b/") else None
            if path:
                ops.setdefault(path, [])
            i += 1
            continue
        m = HUNK.match(line)
        if m and path:
            base_pos = int(m.group(1)) - 1 if int(m.group(2) or "1") > 0 else int(m.group(1))
            i += 1
            cur_start = None
            cur_new: list[str] = []
            cur_del = 0

            def flush(target: str = path) -> None:
                nonlocal cur_start, cur_new, cur_del
                if cur_start is not None:
                    ops[target].append((cur_start, cur_start + cur_del, cur_new))
                cur_start, cur_new, cur_del = None, [], 0

            while i < len(lines) and not lines[i].startswith(("@@", "diff ", "--- ", "+++ ")):
                body = lines[i]
                if body.startswith("\\"):  # "\ No newline at end of file"
                    i += 1
                    continue
                tag, content = body[:1], body[1:]
                if tag == " " or body == "\n":
                    flush()
                    base_pos += 1
                elif tag == "-":
                    if cur_start is None:
                        cur_start = base_pos
                    cur_del += 1
                    base_pos += 1
                elif tag == "+":
                    if cur_start is None:
                        cur_start = base_pos
                    cur_new.append(content)
                i += 1
            flush()
            continue
        i += 1
    return ops


def merge_ops(base: list[str], groups: list[tuple[str, list[tuple[int, int, list[str]]]]]) -> tuple[list[str] | None, list[str]]:
    flat = []
    for order, (tag, ops) in enumerate(groups):
        for start, end, new in ops:
            flat.append((start, end, order, tag, new))
    # insertions (start == end) sort before replacements at the same start
    flat.sort(key=lambda t: (t[0], 0 if t[0] == t[1] else 1, t[2]))
    conflicts = []
    for a in range(len(flat)):
        for b in range(a + 1, len(flat)):
            s1, e1, _, t1, _ = flat[a]
            s2, e2, _, t2, _ = flat[b]
            if s1 < e1 and s2 < e2 and s1 < e2 and s2 < e1:
                conflicts.append(f"replace overlap: {t1} base[{s1}:{e1}] vs {t2} base[{s2}:{e2}]")
            elif s1 == e1 and s2 < s1 < e2 or s2 == e2 and s1 < s2 < e1:
                conflicts.append(f"insert inside a replaced range: {t1} base[{s1}:{e1}] vs {t2} base[{s2}:{e2}]")
    if conflicts:
        return None, conflicts
    out: list[str] = []
    pos = 0
    for start, end, _, _, new in flat:
        out.extend(base[pos:start])
        out.extend(new)
        pos = max(pos, end, start)
    out.extend(base[pos:])
    return out, []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("patches", nargs="+")
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    per_file: dict[str, list[tuple[str, list[tuple[int, int, list[str]]]]]] = {}
    for pfile in args.patches:
        p = Path(pfile)
        for path, ops in parse_patch(p.read_text(encoding="utf-8")).items():
            per_file.setdefault(path, []).append((p.stem, ops))

    failed = False
    results: dict[str, list[str]] = {}
    for path, groups in sorted(per_file.items()):
        proc = subprocess.run(["git", "-C", args.repo, "show", f"{args.base}:{path}"], capture_output=True, text=True)
        base = proc.stdout.splitlines(keepends=True) if proc.returncode == 0 else []
        merged, conflicts = merge_ops(base, groups)
        tags = ", ".join(t for t, _ in groups)
        if conflicts:
            failed = True
            print(f"CONFLICT {path} ({tags}):")
            for c in conflicts:
                print(f"    {c}")
            continue
        results[path] = merged
        dst = out / path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("".join(merged), encoding="utf-8")
        print(f"{path}: {tags}{'  MULTI' if len(groups) > 1 else ''}")

    if failed:
        print("not applying: resolve conflicts first", file=sys.stderr)
        return 1
    if args.apply:
        for path, merged in results.items():
            dst = Path(args.repo) / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text("".join(merged), encoding="utf-8")
        print(f"applied {len(results)} files into {args.repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
