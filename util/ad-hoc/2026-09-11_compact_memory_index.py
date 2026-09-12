#!/usr/bin/env python3
"""2026-09-11_compact_memory_index.py -- fold MEMORY.md singletons into themed groups.

Project: juniper-ml
Sub-Project: session memory maintenance
Application: ad-hoc repair
Author: Paul Calnon
License: MIT License

WHY

`MEMORY.md` is the index loaded into every session, and it is read-capped. At 21.1 KB it was
approaching the 24.4 KB limit, past which the index that exists to be read stops being read.

WHY FOLD RATHER THAN REWRITE

The index already has the right shape -- themed lines carrying several links each
("Verification discipline: ...", "CI/merge mechanics: ..."). Rewriting it by hand to save
bytes risks DROPPING A LINK, and a dropped link is worse than a large file: the memory file
still exists on disk, but nothing points at it, so it is never recalled and never noticed. A
programmatic fold cannot lose one, and this asserts that it did not.

WHAT IT DOES

Appends named singleton lines onto a named group line, then deletes them. Groups and members
are declared below; every member is matched by a UNIQUE substring, and a member that matches
zero or many lines ABORTS the whole run rather than being skipped -- a partial fold would
leave the index half-reorganised and the operator none the wiser.

POST-CONDITION: the set of `](*.md)` targets is IDENTICAL before and after. Byte count falls;
link set does not move.

Usage:
    python3 util/ad-hoc/2026-09-11_compact_memory_index.py            # dry run
    python3 util/ad-hoc/2026-09-11_compact_memory_index.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MEMORY = Path(
    "/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/MEMORY.md"
)

# group anchor (unique substring of the target line) -> members (unique substrings)
GROUPS = {
    "Verification discipline:": [
        "Verify the ENCLOSING FUNCTION",
        "An inconvenient result invites an invented mechanism",
        "Lifecycle probe is non-discriminating",
        "Probe the endpoints before the matrix",
        "A git_sha stamp LIES",
        "Truthiness" if False else "Silent no-op exclusion flags",
        "\"Latent\" is a consumer-graph claim",
    ],
    "CI/merge mechanics:": [
        "Squash ships first commit only",
        "Check main CI green before blaming a PR",
        "skip-ci marker orphans PR checks",
        "Stale PR reverts a shipped contract",
        "canopy X7 timing tests flake",
        "Executor agent invents PR numbers",
        "Release-train ceremony traps",
        "Headless merge](project_branch_protection",
    ],
    "Process/runtime traps:": [
        "/tmp is tmpfs",
        "ps cmdline leaks aescrypt passphrase",
        "Mutation-check traps",
        "@dataclass in a path-loaded module",
        "Tests after `__main__` are invisible",
    ],
    "Worktree + pre-commit:": [
        "Stale editable install after cleanup",
        "Worktree/branch cleanup playbook",
        "Cleanup needs explicit merge signal",
    ],
    "Perf lane": [
        "PF-8 located 2026-09-10",
        "Experiment YAML `runtime:` block binds NOTHING",
        "A pin applied in a CONSTRUCTOR",
        "Drift band 13-20.5% STANDS",
    ],
    "X_val SHIPPED end-to-end": [
        "A defect can live in X_train ONLY",
        "Two S-numbering schemes in the partition arc",
        "Validation bypass + rounding loss",
        "h5py attrs come back as NumPy scalars",
    ],
    "Canopy E2E arc": [
        "Dash layout census proves store instances",
        "Canopy browser driving: force-click",
        "WS:Reconnecting badge is a red herring",
        "dash-renderer 12-slot starvation",
    ],
}


def _find(lines: list, needle: str) -> int:
    hits = [i for i, l in enumerate(lines) if needle in l]
    if len(hits) != 1:
        raise AssertionError(f"{needle!r} matched {len(hits)} line(s), expected exactly 1")
    return hits[0]


def links(text: str) -> set:
    return set(re.findall(r"\]\(([a-z0-9_.-]+\.md)\)", text))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    original = MEMORY.read_text(encoding="utf-8")
    before_links = links(original)
    lines = original.split("\n")

    drop: set = set()
    for anchor, members in GROUPS.items():
        try:
            ai = _find(lines, anchor)
        except AssertionError as exc:
            print(f"group anchor: {exc}", file=sys.stderr)
            return 2
        additions = []
        for m in members:
            try:
                mi = _find(lines, m)
            except AssertionError as exc:
                print(f"member of {anchor!r}: {exc}", file=sys.stderr)
                return 2
            if mi == ai or mi in drop:
                print(f"member {m!r} resolves to the anchor or a used line -- refusing",
                      file=sys.stderr)
                return 2
            additions.append(lines[mi].lstrip("- ").strip())
            drop.add(mi)
        lines[ai] = lines[ai].rstrip() + "; " + "; ".join(additions)

    out = "\n".join(l for i, l in enumerate(lines) if i not in drop)
    after_links = links(out)

    lost = before_links - after_links
    gained = after_links - before_links
    print(f"lines {len(lines)} -> {len(lines) - len(drop)}  ({len(drop)} folded)")
    print(f"bytes {len(original)} -> {len(out)}  ({len(original) - len(out)} saved)")
    print(f"links {len(before_links)} -> {len(after_links)}; LOST {len(lost)}, gained {len(gained)}")
    if lost:
        print("REFUSING -- links lost:", sorted(lost), file=sys.stderr)
        return 2

    if not args.apply:
        print("\ndry run -- pass --apply to write")
        return 0
    MEMORY.write_text(out, encoding="utf-8")
    print(f"\napplied: {MEMORY} is now {len(out)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
