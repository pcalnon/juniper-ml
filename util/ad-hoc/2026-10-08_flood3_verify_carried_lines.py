#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc
# File Name:     2026-10-08_flood3_verify_carried_lines.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Description:
#    Single-use helper for the Cursor flood #3 evaluation (cascor-deploy slice). End-to-end check
#    for a consolidation: every line a SOURCE diff adds must be present in the RESULT file. Per-hunk
#    apply success proves nothing about content that never landed (fleet consolidation trap #4).
#    Lines that are absent are LISTED, never skipped, so each one can be matched to a deliberate
#    correction. Blank and whitespace-only added lines are counted but not checked.
#
#    Usage: 2026-10-08_flood3_verify_carried_lines.py <worktree root> <label=diff> [<label=diff> ...]
#    Exit 0 always; read the MISSING lines.
#####################################################################################################################################################################################################
from __future__ import annotations

import sys
from pathlib import Path


def added_lines(diff_text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    current = None
    for line in diff_text.split("\n"):
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
            if current is not None:
                out.setdefault(current, [])
            continue
        if current is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            out[current].append(line[1:])
    return out


def main() -> int:
    root = Path(sys.argv[1])
    for spec in sys.argv[2:]:
        label, path = spec.split("=", 1)
        per_file = added_lines(Path(path).read_text(encoding="utf-8"))
        total = checked = 0
        missing: list[tuple[str, str]] = []
        for rel, adds in per_file.items():
            target = root / rel
            result_lines = {ln.rstrip() for ln in target.read_text(encoding="utf-8").split("\n")} if target.exists() else set()
            for a in adds:
                total += 1
                if not a.strip():
                    continue
                checked += 1
                if a.rstrip() not in result_lines:
                    missing.append((rel, a))
        print(f"[{label}] added={total} checked={checked} present={checked - len(missing)} MISSING={len(missing)}")
        for rel, a in missing:
            print(f"    MISSING {rel}: {a.strip()[:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
