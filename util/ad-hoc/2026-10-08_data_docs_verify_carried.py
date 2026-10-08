#!/usr/bin/env python3
"""Check that every line a source docs PR adds is present in the consolidated worktree.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc evaluation helper for juniper-data)
Application:  Cursor-fleet flood #3 evaluation (agent data-docs)
Author:       Paul Calnon (generated with Claude Code)
Version:      0.1.0
License:      MIT License

Single-use. Per-hunk "applied cleanly" proves nothing about content that never reached a hunk
(juniper-ml memory: fleet PR consolidation trap 4). This re-derives every added line from each
source diff and looks it up, whole-line, in the result file of the same path. Every miss is
printed so it can be adjudicated as a deliberate correction or a loss.

    python3 util/ad-hoc/2026-10-08_data_docs_verify_carried.py WORKTREE NNN=path/to/diff ...
"""

import os
import sys


def added_lines(diff_text: str):
    path = None
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            continue
        if line.startswith("+++ ") or line.startswith("--- "):
            continue
        if line.startswith("+") and path:
            body = line[1:]
            if body.strip():
                yield path, body


def main() -> int:
    worktree = sys.argv[1]
    total_missing = 0
    for spec in sys.argv[2:]:
        label, diff_path = spec.split("=", 1)
        with open(diff_path, encoding="utf-8") as fh:
            diff_text = fh.read()
        cache: dict[str, set[str]] = {}
        n = missing = 0
        for path, body in added_lines(diff_text):
            if path not in cache:
                full = os.path.join(worktree, path)
                if os.path.exists(full):
                    with open(full, encoding="utf-8") as fh:
                        cache[path] = set(fh.read().splitlines())
                else:
                    cache[path] = set()
            n += 1
            if body not in cache[path]:
                missing += 1
                print(f"  MISSING #{label} {path}: {body[:150]}")
        total_missing += missing
        print(f"#{label}: {n} added lines, {missing} not present verbatim")
    print(f"TOTAL not present verbatim: {total_missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
